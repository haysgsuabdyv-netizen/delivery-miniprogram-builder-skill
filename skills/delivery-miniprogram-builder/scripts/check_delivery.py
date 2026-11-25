#!/usr/bin/env python3
"""Validate the decision file and the traceable delivery bundle.

Usage:
    python check_delivery.py <delivery-dir>
    python check_delivery.py <delivery-dir> --json

Two delivery documents are expected in the directory:
    00-开工判断与决策清单.md   main decision file for the project lead
    01-开发接手包.md           bundle for developers, with # 00 .. # 04 sections

The script checks the fact-block/decision requirements in the main file and the
cross-stage chain (sources -> features -> pages -> brand tokens -> acceptance)
inside the bundle. Sections marked 未启动 are checked for honest deferral rather
than for a fabricated ID chain. It does NOT judge whether conclusions are good.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOCUMENTS = {
    "main": "00-开工判断与决策清单.md",
    "bundle": "01-开发接手包.md",
}
STAGE_KEYS = ("00", "01", "02", "03", "04")
STAGE_RE = re.compile(r"^#\s+(0[0-4])\s+", re.M)
CONCLUSION_RE = re.compile(r"^\s*结论[：:]\s*(部分继续|继续|暂缓)", re.M)
DECISION_IDS = re.compile(r"\b(?:V|F|X|P|M|D|I|T|BT)-\d{2}\b")

# Which bundle section is allowed to define each ID family.
HOME = {
    "R": "00", "B": "00", "C": "00", "E": "00",
    "V": "01", "F": "01", "X": "01",
    "P": "02", "M": "02", "D": "02", "I": "02",
    "T": "03", "BT": "03",
}

TOKEN = r"(?:BT|R|B|C|E|V|F|X|P|M|D|I|T)-\d{2}"
ID_RE = re.compile(r"\b(" + TOKEN + r")\b")
# A definition line starts with an ID followed by a table pipe, colon or dash.
# This keeps prose like "BT-01 至 BT-05 逐项..." from being read as a definition.
DEFINE_RE = re.compile(r"^(" + TOKEN + r")\*{0,2}\s*(?:\||:|：|—|-)")
BRACKET_REF_RE = re.compile(r"\[([^\]]*)\]")
GENERIC_PAGE_WORDS = {"首页", "分类", "购物车", "我的", "个人中心", "商品列表", "商品详情"}


def family(token: str) -> str:
    return token.rsplit("-", 1)[0]


def defined_ids(text: str) -> set[str]:
    """An ID is defined when it starts a table cell or list line."""
    found = set()
    for line in text.splitlines():
        stripped = line.strip().lstrip("|-*#> ").strip().lstrip("*").strip()
        m = DEFINE_RE.match(stripped)
        if m:
            found.add(m.group(1))
    return found


def defined_lines(text: str) -> list[tuple[str, str]]:
    """Return (id, full line) for every definition line."""
    rows = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("|-*#> ").strip().lstrip("*").strip()
        m = DEFINE_RE.match(stripped)
        if m:
            rows.append((m.group(1), line))
    return rows


def refs_in(line: str) -> set[str]:
    """Only bracketed inline references count as evidence."""
    result = set()
    for chunk in BRACKET_REF_RE.findall(line):
        result.update(ID_RE.findall(chunk))
    return result


def all_refs(text: str) -> set[str]:
    result = set()
    for chunk in BRACKET_REF_RE.findall(text):
        result.update(ID_RE.findall(chunk))
    return result


def skipped(text: str) -> bool:
    return "未启动" in text


def split_bundle(text: str) -> dict[str, str]:
    """Split the bundle on its '# 00 ...' .. '# 04 ...' section headings."""
    matches = list(STAGE_RE.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[m.group(1)] = text[m.start():end]
    return sections


def read_documents(root: Path) -> tuple[str, str, list[str]]:
    main_text, bundle_text, missing = "", "", []
    for key, name in DOCUMENTS.items():
        path = root / name
        if path.is_file():
            content = path.read_text(encoding="utf-8", errors="replace")
            if key == "main":
                main_text = content
            else:
                bundle_text = content
        else:
            missing.append(name)
    return main_text, bundle_text, missing


def run_checks(root: Path) -> dict:
    checks: list[dict] = []

    def add(name: str, passed: bool, evidence: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "evidence": evidence})

    main_text, bundle_text, missing = read_documents(root)
    add(
        "两份交付文档齐备（主文件 + 附件）",
        not missing,
        "齐备" if not missing else "缺少：" + "、".join(missing),
    )
    if missing:
        return _result(root, checks, "unknown")

    conclusion = CONCLUSION_RE.search(main_text)
    mode = conclusion.group(1) if conclusion else "unknown"
    add(
        "主文件写明了开工结论（继续 / 暂缓 / 部分继续）",
        mode != "unknown",
        f"结论={mode}",
    )

    # --- Main decision file: fact blocks, gaps, conflicts, evidence ---
    add(
        "主文件包含事实分块与状态标注",
        "事实分块" in main_text and any(
            s in main_text for s in ("已确认", "待确认", "前后冲突")
        ),
        "事实块需逐条标注已确认 / 待确认 / 前后冲突",
    )
    add(
        "主文件返工风险清单含责任人与补齐标准",
        all(k in main_text for k in ("谁来补", "补到什么程度", "不补的后果")),
        "缺口需写明谁来补、补到什么程度才能继续、不补的后果",
    )
    add(
        "主文件包含证据索引（可回溯到原文）",
        "证据索引" in main_text and "原文摘录" in main_text,
        "每条结论要能翻回资料的文件名与锚点",
    )
    conflict_declared = "前后冲突" in main_text
    add(
        "冲突项并列保留各方原文，未静默择一",
        (not conflict_declared) or ("版本 A" in main_text and "版本 B" in main_text),
        "未声明冲突" if not conflict_declared else (
            "并列两版" if "版本 A" in main_text and "版本 B" in main_text else "缺少版本 A / 版本 B 并列"
        ),
    )

    # --- Bundle structure ---
    sections = split_bundle(bundle_text)
    missing_sections = [k for k in STAGE_KEYS if k not in sections]
    add(
        "附件包含 00–04 五个章节",
        not missing_sections,
        "齐备" if not missing_sections else "缺少章节：" + "、".join(missing_sections),
    )
    if missing_sections:
        return _result(root, checks, mode)
    docs = sections

    defs = {k: defined_ids(v) for k, v in docs.items()}

    # --- 00: source ledger (always checked) ---
    r_ids = {i for i in defs["00"] if family(i) in {"R", "B", "C", "E"}}
    has_r = any(family(i) == "R" for i in r_ids)
    has_b = any(family(i) == "B" for i in r_ids)
    add(
        "00 台账登记了需求来源 R",
        has_r,
        f"定义 {len(r_ids)} 个来源项；R={has_r}",
    )
    add(
        "00 台账登记品牌来源 B 或明确列为待补",
        has_b or "待补" in docs["00"] or "待补" in main_text,
        f"B={has_b}；缺品牌资料时须列待补，不得编造",
    )
    add(
        "00 台账包含待补清单或冲突说明",
        "待补" in docs["00"] or "冲突" in docs["00"] or "待补" in main_text,
        "用于暴露资料缺口，避免以臆测补齐",
    )
    add(
        "00 台账每条来源都标注了状态",
        "状态" in docs["00"],
        "状态区分已确认 / 待确认 / 前后冲突",
    )

    source_defs = {i for i in defs["00"] if family(i) in {"R", "B", "C", "E"}}

    # --- 01/02/03: either a real chain or an honest deferral ---
    for key, label in (("01", "价值与功能判断"), ("02", "架构设计"), ("03", "品牌与搭建")):
        if skipped(docs[key]):
            fabricated = sorted(
                i for i in defs[key] if family(i) not in {"R", "B", "C", "E"}
            )
            add(
                f"{key} {label}标注未启动且未编造编号",
                not fabricated,
                "未启动：待补齐" if not fabricated else "出现臆造编号：" + ", ".join(fabricated),
            )
        else:
            add(
                f"{key} {label}已启动",
                True,
                "进入链路校验",
            )

    s01, s02, s03 = skipped(docs["01"]), skipped(docs["02"]), skipped(docs["03"])

    # 01: value/feature conclusions and traceability
    if not s01:
        v_ids = {i for i in defs["01"] if family(i) == "V"}
        f_ids = {i for i in defs["01"] if family(i) == "F"}
        x_ids = {i for i in defs["01"] if family(i) == "X"}
        add(
            "01 定义了价值点与功能清单",
            bool(v_ids) and bool(f_ids) and bool(x_ids),
            f"V={len(v_ids)}, F={len(f_ids)}, X={len(x_ids)}（该做/不做两侧都要有）",
        )
        conclusions = [
            (i, line) for i, line in defined_lines(docs["01"]) if family(i) in {"V", "F", "X"}
        ]
        bad = [
            i for i, line in conclusions
            if not any(family(r) in {"R", "C"} for r in refs_in(line))
        ]
        add(
            "01 每条价值/功能/排除结论都有需求或合规依据",
            bool(conclusions) and not bad,
            f"共 {len(conclusions)} 条结论，缺依据：{', '.join(bad) if bad else '无'}",
        )
        add(
            "01 存在需求覆盖矩阵",
            "覆盖矩阵" in docs["01"],
            "覆盖矩阵用于证明不漏已确认需求",
        )
        unresolved_01 = sorted(
            r for r in all_refs(docs["01"])
            if family(r) in {"R", "B", "C", "E"} and r not in source_defs
        )
        add(
            "01 引用的来源编号都能在 00 台账找到",
            not unresolved_01,
            "无法解析：" + ", ".join(unresolved_01) if unresolved_01 else "全部可解析",
        )

    # 02: architecture derived from features
    if not s02:
        p_ids = {i for i in defs["02"] if family(i) == "P"}
        m_ids = {i for i in defs["02"] if family(i) == "M"}
        d_ids = {i for i in defs["02"] if family(i) == "D"}
        add(
            "02 定义了页面、模块与数据实体",
            bool(p_ids) and bool(m_ids) and bool(d_ids),
            f"P={len(p_ids)}, M={len(m_ids)}, D={len(d_ids)}",
        )
        page_lines = [(i, line) for i, line in defined_lines(docs["02"]) if family(i) == "P"]
        orphan_pages = [
            i for i, line in page_lines if not any(family(r) == "F" for r in refs_in(line))
        ]
        add(
            "02 每个页面都标注派生自哪个功能 F",
            bool(page_lines) and not orphan_pages,
            f"共 {len(page_lines)} 个页面，无派生依据：{', '.join(orphan_pages) if orphan_pages else '无'}",
        )
        f_ids_01 = {i for i in defs["01"] if family(i) == "F"} if not s01 else set()
        unresolved_f = sorted(
            r for r in all_refs(docs["02"]) if family(r) == "F" and r not in f_ids_01
        )
        add(
            "02 引用的功能编号都能在 01 找到",
            not unresolved_f,
            "无法解析：" + ", ".join(unresolved_f) if unresolved_f else "全部可解析",
        )
        add("02 存在功能到页面的链路表", "链路表" in docs["02"], "链路表是逐段核对的骨架")
        generic_hits = []
        for _id, line in page_lines:
            cells = [c.strip() for c in line.split("|")]
            if len(cells) > 2 and cells[2] in GENERIC_PAGE_WORDS:
                generic_hits.append(cells[2])
        add(
            "02 页面清单不是通用四模块骨架",
            len(generic_hits) < 3,
            "通用页面名：" + ", ".join(generic_hits) if generic_hits else "未见通用骨架页面",
        )
    add(
        "链路顺序：02 启动时 01 不能仍标注未启动",
        not (not s02 and s01),
        "链路断裂：01 未启动而 02 已启动" if (not s02 and s01) else "顺序正常",
    )

    # 03: brand tokens and template decisions
    if not s03:
        t_ids = {i for i in defs["03"] if family(i) == "T"}
        bt_ids = {i for i in defs["03"] if family(i) == "BT"}
        add(
            "03 定义了模板决策与品牌落地项",
            bool(t_ids) and bool(bt_ids),
            f"T={len(t_ids)}, BT={len(bt_ids)}",
        )
        bt_lines = [(i, line) for i, line in defined_lines(docs["03"]) if family(i) == "BT"]
        bad_bt = [
            i for i, line in bt_lines if not any(family(r) == "B" for r in refs_in(line))
        ]
        add(
            "03 每个品牌落地项都有品牌资料依据",
            bool(bt_lines) and not bad_bt,
            f"共 {len(bt_lines)} 项，缺依据：{', '.join(bad_bt) if bad_bt else '无'}",
        )
        add(
            "03 有临时值/待补项的显式标注或已全部确认",
            ("待补" in docs["03"] or "临时值" in docs["03"]) or not any(
                "待补" in line for line in docs["00"].splitlines()
            ),
            "品牌资料缺失时不得用通用默认值冒充",
        )
        add(
            "03 声明交接给内置 mini-program-development",
            "mini-program-development" in docs["03"],
            "本 Skill 不重造原生工程与发布链",
        )
        unresolved_b = sorted(
            r for r in all_refs(docs["03"]) if family(r) == "B" and r not in source_defs
        )
        add(
            "03 引用的品牌编号都能在 00 台账找到",
            not unresolved_b,
            "无法解析：" + ", ".join(unresolved_b) if unresolved_b else "全部可解析",
        )

    add(
        "链路顺序：03 启动时 02 不能仍标注未启动",
        not (not s03 and s02),
        "链路断裂：02 未启动而 03 已启动" if (not s03 and s02) else "顺序正常",
    )

    # --- 04: honest deferral or the regular acceptance checklist ---
    acceptance = docs["04"]
    if mode == "暂缓" and re.search(r"(?m)^\s*未启动\s*[：:]", acceptance):
        add(
            "04 验收标注未启动且未编造编号",
            DECISION_IDS.search(acceptance) is None,
            "暂缓时保留 04 章节，标明待补齐。",
        )
    else:
        needed = [
            "判断有依据", "架构来自资料", "品牌一致", "可串联",
            "资料不全仍能开工判断", "冲突不静默择一",
        ]
        missing_items = [k for k in needed if k not in docs["04"]]
        add(
            "04 验收清单覆盖六条验收标准",
            not missing_items,
            "缺少：" + "、".join(missing_items) if missing_items else "六条齐备",
        )
        add(
            "04 如实记录已执行与未执行的校验",
            ("校验" in docs["04"]) and (
                "未执行" in docs["04"] or "未跑" in docs["04"] or "待联调" in docs["04"]
                or "未启动" in docs["04"]
            ),
            "不把没跑过的编译/预览/联调写成通过",
        )

    # --- Cross-mode consistency ---
    if mode == "暂缓":
        add(
            "暂缓结论与附件一致（01–03 均未启动）",
            s01 and s02 and s03,
            f"01={s01}, 02={s02}, 03={s03}（暂缓时不得凑编号链）",
        )
        add(
            "暂缓时主文件列出了补齐责任",
            "谁来补" in main_text and "补到什么程度" in main_text,
            "暂缓要能直接转成一次对客户的追问",
        )
    elif mode == "继续":
        add(
            "继续结论与附件一致（01–03 均已启动）",
            not (s01 or s02 or s03),
            "结论为继续时三段都应有成果",
        )
    elif mode == "部分继续":
        add(
            "部分继续结论写明先做与待补的边界",
            "可以继续的部分" in main_text and "必须等补齐的部分" in main_text,
            "部分继续要点明哪些段先做、哪些必须等补齐",
        )

    return _result(root, checks, mode)


def _result(root: Path, checks: list[dict], mode: str) -> dict:
    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    return {
        "delivery_dir": str(root),
        "mode": mode,
        "checks": checks,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate": round(passed / total, 3) if total else 0.0,
        },
        "verdict": "PASS" if passed == total else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验开工判断与交付链路是否闭合")
    parser.add_argument("delivery_dir", type=Path, help="交付目录（含主文件与附件两份文档）")
    parser.add_argument("--json", action="store_true", help="只输出 JSON")
    args = parser.parse_args()

    result = run_checks(args.delivery_dir)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"交付目录：{result['delivery_dir']}")
        print(f"开工结论：{result['mode']}")
        for c in result["checks"]:
            mark = "PASS" if c["passed"] else "FAIL"
            print(f"  [{mark}] {c['name']} — {c['evidence']}")
        s = result["summary"]
        print(f"\n{s['passed']}/{s['total']} 通过，结论：{result['verdict']}")
        print("脚本只检查链路与事实分块是否闭合，结论质量仍需人工复核。")

    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
