# 微信小程序签约后交付 Skill

把已签约客户的合同、会议纪要、原型或品牌资料整理成开工判断和开发接手包。工作流会保留证据出处、待确认事项和返工风险。

## 安装

在 Codex 中发送这条提示即可安装整套文件。

> 请从 https://github.com/haysgsuabdyv-netizen/delivery-miniprogram-builder-skill/tree/main/skills/delivery-miniprogram-builder 安装 `delivery-miniprogram-builder` Skill，连同目录里的模板、参考资料和校验脚本一起安装。

也可通过 [GitHub Releases](https://github.com/haysgsuabdyv-netizen/delivery-miniprogram-builder-skill/releases) 下载源码 ZIP，解压后将 `skills/delivery-miniprogram-builder` 文件夹导入支持 Agent Skills 的工具。

## 开始使用

上传至少一份该客户的真实交付资料，然后告诉助手：

> 用 `delivery-miniprogram-builder` 检查这个已签约小程序项目能否开工。按已确认、待确认和前后冲突整理材料，列出返工风险、补齐责任和开工结论。把目前能继续的部分写进开发接手包。

交付物包括 `00-开工判断与决策清单.md`、`01-开发接手包.md`，以及运行校验脚本后生成的 `verification.json`。

## 环境要求

生成开工判断和开发规格需要支持 Agent Skills 的工具。运行交付校验需要 Python 3。使用内置能力完成原生小程序搭建、云服务配置、预览和发布需要 WorkBuddy 的 `mini-program-development`。

## 许可证

本项目采用 [MIT 许可](LICENSE)。

## 署名

- Gavin·he
- 华骏睿
- 王文华
- 鲁思成
