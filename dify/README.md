# HallucC — AI Hallucination Detection & Safety for Dify

**Author:** fredyee · **Version:** 0.1.0 · **Type:** tool plugin
**Source repository:** <https://github.com/fredyee/hallucc-plugins> (`dify/`)

HallucC (https://aihcc.cloud) brings production-grade AI content verification into your
Dify workflows and agents. All detection runs on the HallucC cloud API — this plugin is
a thin client; no model or search logic runs locally.

## Tools

| Tool | What it does |
|---|---|
| **Hallucination Detection** (`halluc_detect`) | Verifies factual claims in AI-generated text with multi-source search. Each claim is labeled ✅ supported / ⚠️ unverified / ❌ refuted with evidence sources and an overall hallucination-risk score. |
| **Agent Trajectory Evaluation** (`halluc_detect_trajectory`) | Audits a full agent execution trajectory (per-step thought/action/observation), not just the final answer. Six-dimension scoring, failure-mode codes, hallucination propagation DAG. |
| **AI Safety Guard** (`guard_check`) | OWASP LLM Top 10 aligned safety gate: prompt injection, jailbreak, harmful content, sensitive-data leakage, fraud. |
| **CUA Action Risk Classification** (`cua_classify`) | Classifies Computer-Use Agent (GUI) actions L0–L3 (allow / log / confirm / block) plus `takeover` (credential scenarios suspend and wait for the user to type it themselves). Pure rule engine — free, no quota cost, safe for high-frequency calls. |
| **CUA Code Audit** (`cua_audit_code`) | Static-analyzes Agent source code for dangerous imports, permission boundaries, injection surfaces, dangerous defaults, sandbox absence. Pure rule engine — free, no quota cost. |

## Setup

1. Install the plugin in Dify (Marketplace, GitHub, or local `.difypkg` upload).
2. Create an API key at <https://aihcc.cloud/keys> (format `hc_xxxxxxxx`).
3. Paste the key into the plugin's credentials dialog. The key is validated
   against the free `/cua/classify` endpoint, so validation consumes no quota.

## Usage notes

- **Speed modes** on detection tools: `fast` (rule-only, ~200 ms), `standard` (~5 s),
  `deep` (multi-model cross-validation, ~15 s).
- **Domain profiles**: general / medical / legal / finance / education / government —
  each ships trusted-source lists and prompt hints tuned for the vertical.
- **Trajectory input** is a JSON array of steps
  `[{"step":1,"thought":"...","action":"...","action_input":"...","observation":"..."}, ...]`
  (1–20 steps, `final_answer` on the last step). In a Dify workflow, assemble it in a
  Code node from upstream node execution records.
- **CUA actions input** is a lenient JSON array: `{"x":100,"y":200}` implies a click;
  pyautogui-style names (`press`, `hotkey`, `write`, `typewrite`, `move`,
  `doubleclick`, `scroll`…) are normalized automatically.
- **Multi-agent delegation chains**: each action may optionally carry `chain_id` /
  `agent_id` / `parent_agent_id` / `delegation_depth`, in which case the backend appends a
  cross-agent propagation analysis (the chain aggregate level is raised to L3 and
  `risk_diluted` is set when cross-hop propagation exists) under the `chain_trace` field;
  omit them and behaviour is unchanged.
- **CUA rules covered**: sensitive paths, destructive commands, irreversible element
  semantics, domain grading (unknown-domain navigation L2; blacklisted domains and
  sensitive paste to non-allowlisted domains L3; payment amounts above threshold L3),
  credential lexicon plus payment/login-domain takeover, and task-intent deviation
  (an action leaving the scope escalates one level — tightening only, never loosening).
  Responses include `ruleset_version` (the rule-set version, so you can verify online
  detection and the local Gate run the same rules) and `disclaimer` (results are a
  grading reference only — nothing is actually blocked).
- `guard_check` with `check_hallucination=true` additionally runs the hallucination
  pipeline and consumes detection quota.

## Billing

Free tier 3 detections/day; Pro ¥49/month (500), Pro+ ¥99/month (2000, incl. CUA
interception); API pay-as-you-go ¥0.1/call. `cua_classify` is free for all users.
Manage quota at <https://aihcc.cloud>.

## Privacy

See [PRIVACY.md](PRIVACY.md).
