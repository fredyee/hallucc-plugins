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


def _format(data: dict) -> str:
    s = data.get("summary") or {}
    lines = [
        f"共 {s.get('total', 0)} 个动作: L0 放行 {s.get('L0', 0)} / L1 记录 {s.get('L1', 0)}"
        f" / L2 需确认 {s.get('L2', 0)} / L3 阻断 {s.get('L3', 0)}",
        "",
    ]
    for r in data.get("results") or []:
        action = (r.get("action") or {}).get("action", "?")
        lines.append(
            f"[{r.get('level', '?')}] step {r.get('step', '?')}: {action} — {r.get('outcome', '')}"
        )
        for reason in (r.get("reasons") or [])[:3]:
            lines.append(f"    · {reason}")
    if data.get("session_id"):
        lines.append(f"---\n审计会话: {data['session_id']}")
    return "\n".join(lines)


class CuaClassifyTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = (self.runtime.credentials.get("api_key") or "").strip()
        if not api_key:
            raise RuntimeError(
                "HallucC API Key is missing. Configure it in the plugin settings."
            )
        raw = (tool_parameters.get("actions") or "").strip()
        if not raw:
            raise ValueError("Parameter `actions` is required")
        try:
            actions = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"`actions` must be a JSON array of action objects, parse error: {e}"
            ) from e
        if not isinstance(actions, list) or not actions:
            raise ValueError("`actions` must be a non-empty JSON array")
        payload: dict[str, Any] = {"actions": actions}
        session_id = (tool_parameters.get("session_id") or "").strip()
        if session_id:
            payload["session_id"] = session_id
        data = _post("/cua/classify", payload, api_key)
        yield self.create_text_message(_format(data))
        yield self.create_json_message(data)
