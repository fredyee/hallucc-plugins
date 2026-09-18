import json
from collections.abc import Generator
from typing import Any

import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

API_BASE = "https://aihcc.cloud/api"


def _post(path: str, payload: dict, api_key: str) -> dict:
    try:
        resp = requests.post(
            f"{API_BASE}{path}",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=115,
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to reach HallucC API: {e}") from e
    if resp.status_code == 401:
        raise RuntimeError(
            "HallucC API Key invalid or expired. Manage keys at https://aihcc.cloud/keys"
        )
    if resp.status_code == 429:
        raise RuntimeError(
            "HallucC quota exhausted or rate limited. See https://aihcc.cloud/pricing"
        )
    if resp.status_code != 200:
        raise RuntimeError(f"HallucC API error {resp.status_code}: {resp.text[:500]}")
    return resp.json()


def _score(v: Any) -> Any:
    """Dimension values may be plain numbers or {score, ...} dicts."""
    if isinstance(v, dict):
        return v.get("score", v)
    return v


def _format(data: dict) -> str:
    s = data.get("summary") or {}
    lines = [
        f"轨迹步数: {s.get('total_steps', 0)} | 幻觉步: {s.get('hallucinated_steps', 0)}"
        f" | 干净步: {s.get('clean_steps', 0)} | 传播链: {s.get('propagation_chains', 0)}",
        f"LLM 调用: {s.get('llm_calls', 0)} | 搜索调用: {s.get('search_calls', 0)}"
        + (" | ⚠️ 已达 LLM 调用上限被截断" if s.get("truncated") else ""),
    ]
    dims = s.get("dimensions") or data.get("agent_eval") or {}
    if isinstance(dims, dict) and dims:
        lines.append("\n六维评分:")
        for k, v in dims.items():
            lines.append(f"  - {k}: {_score(v)}")
    fms = data.get("failure_modes") or []
    if fms:
        lines.append("\n失败模式:")
        for fm in fms:
            lines.append(
                f"  - [{fm.get('severity', '')}] step {fm.get('step', '?')}: {fm.get('code', '')}"
            )
    prop = data.get("propagation") or []
    if prop:
        lines.append("\n幻觉传播 DAG:")
        for edge in prop[:10]:
            if isinstance(edge, dict):
                lines.append(
                    f"  - step {edge.get('from_step', '?')} → {edge.get('to_steps', '')}"
                )
    for key, label in (("cua_gui_steps", "GUI 动作步"), ("cua_risky_steps", "危险动作步 (L2/L3)"), ("cua_escalated_steps", "幻觉驱动升级步")):
        if s.get(key):
            lines.append(f"{label}: {s[key]}")
    quota = data.get("quota") or {}
    if quota:
        remaining = quota.get("remaining")
        lines.append(
            f"---\n额度: {quota.get('plan', '')} · 今日剩余 "
            f"{'∞' if remaining is None else remaining}"
        )
    return "\n".join(lines)


class HallucDetectTrajectoryTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = (self.runtime.credentials.get("api_key") or "").strip()
        if not api_key:
            raise RuntimeError(
                "HallucC API Key is missing. Configure it in the plugin settings."
            )
        raw = (tool_parameters.get("trajectory") or "").strip()
        if not raw:
            raise ValueError("Parameter `trajectory` is required")
        try:
            trajectory = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"`trajectory` must be a JSON array of steps, parse error: {e}"
            ) from e
        if not isinstance(trajectory, list) or not trajectory:
            raise ValueError("`trajectory` must be a non-empty JSON array of steps")
        payload: dict[str, Any] = {
            "trajectory": trajectory,
            "speed": tool_parameters.get("speed") or "standard",
            "domain": tool_parameters.get("domain") or "general",
        }
        task = (tool_parameters.get("task") or "").strip()
        if task:
            payload["task"] = task
        data = _post("/detect-agent-trajectory", payload, api_key)
        yield self.create_text_message(_format(data))
        yield self.create_json_message(data)
