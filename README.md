# HallucC Plugins

[HallucC](https://aihcc.cloud) 幻觉检测与 AI 安全能力的各平台插件包。
Platform plugin packages for [HallucC](https://aihcc.cloud) — AI hallucination detection & safety.

## Dify（`dify/`）

原生 Dify 工具插件，4 个工具 / Native Dify tool plugin with 4 tools:

| Tool | 说明 |
|---|---|
| `halluc_detect` | 幻觉检测：多源搜索核验，逐条声明标注 证实/存疑/证伪 |
| `halluc_detect_trajectory` | Agent 轨迹全链路评估：六维评分 + 失败模式 + 幻觉传播 DAG |
| `guard_check` | AI 安全检测：注入/越狱/有害内容（对齐 OWASP LLM Top 10） |
| `cua_classify` | CUA 动作风险分级 L0-L3（纯规则，免费不耗额度） |

安装 / Install：
- Dify Marketplace（审核中 / under review）
- 本仓库 `dify/hallucc.difypkg` 下载后本地安装（Dify → 插件 → 本地上传）
- API Key：<https://aihcc.cloud/keys>

## Coze（`coze/`）

OpenAPI 3.0 单文件，Coze 插件导入 `coze/openapi.yaml`。

---

插件均为纯 HTTP 客户端薄封装，不含核心检测逻辑；所有计算在 `https://aihcc.cloud/api` 完成。
All plugins are thin API clients — no detection logic ships in these packages.
