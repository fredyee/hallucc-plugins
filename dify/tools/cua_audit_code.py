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
        f"能力等级: {s.get('capability_level', '?')}  "
        f"工具数: {s.get('tool_count', 0)}  "
        f"危险导入: {s.get('dangerous_import_count', 0)}  "
        f"注入面: {s.get('injection_surface_count', 0)}",
        f"高危: {s.get('by_severity', {}).get('high', 0)}  "
        f"中危: {s.get('by_severity', {}).get('medium', 0)}  "
        f"低危: {s.get('by_severity', {}).get('low', 0)}",
        "",
    ]
    for f in data.get("findings") or []:
        sev = f.get("severity", "?")
        lines.append(
            f"[{sev}] {f.get('file', '?')}:{f.get('line', '?')} "
            f"({f.get('category', '?')}) — {f.get('detail', '')}"
        )
        if not lines[-1].endswith("— "):
            lines.append(f"    · {f.get('raw', '')}")
    return "\n".join(lines)


class CuaAuditCodeTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = (self.runtime.credentials.get("api_key") or "").strip()
        if not api_key:
            raise RuntimeError(
                "HallucC API Key is missing. Configure it in the plugin settings."
            )

        payload: dict[str, Any] = {}
        code = (tool_parameters.get("code") or "").strip()
        files_raw = (tool_parameters.get("files") or "").strip()

        if files_raw:
            try:
                files = json.loads(files_raw)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"`files` must be a valid JSON array, parse error: {e}"
                ) from e
            if not isinstance(files, list) or not files:
                raise ValueError("`files` must be a non-empty JSON array")
            payload["files"] = files
        elif code:
            payload["code"] = code
            filename = (tool_parameters.get("filename") or "").strip()
            if filename:
                payload["filename"] = filename
        else:
            raise ValueError("Either `code` or `files` is required")

        data = _post("/cua/audit-code", payload, api_key)
        yield self.create_text_message(_format(data))
        yield self.create_json_message(data)
