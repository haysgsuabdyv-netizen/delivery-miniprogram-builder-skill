# 微信小程序签约后交付 Skill

把已签约客户的合同、会议纪要、原型或品牌资料整理成开工判断和开发接手包。工作流会保留证据出处、待确认事项和返工风险。

## 安装

[下载完整安装包 delivery-miniprogram-builder.zip](https://github.com/haysgsuabdyv-netizen/delivery-miniprogram-builder-skill/releases/download/v1.0.0/delivery-miniprogram-builder.zip)

在 **WorkBuddy** 中打开「专家·技能·连接器」，进入「技能」，选择「添加技能」和「上传技能」，选中下载的 ZIP 即可导入。模板、参考资料和校验脚本已随包提供。[WorkBuddy 技能导入说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market#上传技能)

在 **Codex** 中发送下面这句话。

> 请从 https://github.com/haysgsuabdyv-netizen/delivery-miniprogram-builder-skill/tree/v1.0.0/skills/delivery-miniprogram-builder 安装 `delivery-miniprogram-builder` Skill，连同目录里的模板、参考资料和校验脚本一起安装。

## 开始使用

上传至少一份该客户的真实交付资料，然后告诉助手：

> 用 `delivery-miniprogram-builder` 检查这个已签约小程序项目能否开工。按已确认、待确认和前后冲突整理材料，列出返工风险、补齐责任和开工结论。把目前能继续的部分写进开发接手包。

交付物包括 `00-开工判断与决策清单.md`、`01-开发接手包.md`，以及运行校验脚本后生成的 `verification.json`。

## 环境要求

使用支持 Agent Skills 的工具即可整理开工判断和开发规格。运行随包的交付校验脚本时使用 Python 3。

搭建、云服务接入、预览和发布时，Skill 将规格交给支持微信小程序开发的 WorkBuddy，调用它自带的 `mini-program-development`。发布体验版或正式版时，按 WorkBuddy 的提示完成微信小程序账号授权。[WorkBuddy 小程序发布说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/App-Publishing/Mini-Program)

## 许可证

本项目采用 [MIT 许可](LICENSE)。

## 署名

- Gavin·he
- 华骏睿
- 王文华
- 鲁思成
