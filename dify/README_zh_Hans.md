# HallucC — Dify AI 幻觉检测与安全插件

**作者：** fredyee · **版本：** 0.1.0 · **类型：** 工具插件
**源码仓库：** <https://github.com/fredyee/hallucc-plugins>（`dify/` 目录）

HallucC（https://aihcc.cloud）把生产级 AI 内容核验带进 Dify 工作流与 Agent。
所有检测均在 HallucC 云端 API 完成——本插件只是轻量客户端，本地不运行任何模型或检索逻辑。

## 工具一览

| 工具 | 能力 |
|---|---|
| **幻觉检测**（`halluc_detect`） | 多源搜索交叉核验 AI 生成文本中的事实性声明，逐条标注 ✅ 证实 / ⚠️ 存疑 / ❌ 证伪，附来源链接与整体幻觉风险评分。 |
| **Agent 轨迹检测**（`halluc_detect_trajectory`） | 审计 Agent 完整执行轨迹（逐步 thought/action/observation），而非只看最终答案：六维评分、失败模式分类、幻觉传播 DAG。 |
| **AI 安全检测**（`guard_check`） | 对齐 OWASP LLM Top 10 的安全网关：Prompt 注入、越狱、有害内容、敏感信息泄露、欺诈。 |
| **CUA 动作风险分级**（`cua_classify`） | Computer-Use Agent（GUI 操作）动作分级 L0–L3（放行/记录/确认/阻断）。纯规则引擎——免费、不耗额度、可高频调用。 |
| **CUA 代码审计**（`cua_audit_code`） | Agent 源码静态审计：危险导入、权限边界、注入面、危险默认值、沙箱缺失。纯规则引擎——免费、不耗额度。 |

## 配置

1. 在 Dify 安装本插件（Marketplace / GitHub / 本地上传 `.difypkg`）。
2. 到 <https://aihcc.cloud/keys> 创建 API Key（`hc_xxxxxxxx` 格式）。
3. 粘贴到插件凭证弹窗。凭证校验走免费的 `/cua/classify` 端点，不消耗额度。

## 使用说明

- **速度模式**：`fast`（纯规则，约 200ms）、`standard`（约 5s）、`deep`（多模型交叉验证，约 15s）。
- **领域模式**：general / medical / legal / finance / education / government，
  每个领域内置可信来源清单与针对性提示词。
- **轨迹入参**为 JSON 数组：
  `[{"step":1,"thought":"...","action":"...","action_input":"...","observation":"..."}, ...]`
  （1–20 步，末步带 `final_answer`）。在 Dify 工作流中用「代码执行」节点把上游各节点
  执行记录组装成该结构即可。
- **CUA 动作入参**为宽松 JSON 数组：`{"x":100,"y":200}` 自动推断为点击；
  pyautogui 风格动作名（`press`、`hotkey`、`write`、`typewrite`、`move`、
  `doubleclick`、`scroll`…）自动归一化。
- `guard_check` 开启 `check_hallucination` 会额外跑幻觉检测管线，消耗检测额度。

## 计费

免费版每天 2 次检测；Pro ¥49/月（500 次）、Pro 增强 ¥99/月（2000 次，含 CUA 拦截）；
API 按量 ¥0.1/次。`cua_classify` 对所有用户免费。额度管理见 <https://aihcc.cloud>。

## 隐私

见 [PRIVACY.md](PRIVACY.md)。
