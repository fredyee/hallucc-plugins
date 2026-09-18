from collections.abc import Generator
from typing import Any

import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

API_BASE = "https://aihcc.cloud/api"

_STATUS_MARK = {"supported": "✅", "unverified": "⚠️", "refuted": "❌"}


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
    total = s.get("total", 0)
    red = s.get("red", 0)
    yellow = s.get("yellow", 0)
    green = s.get("green", 0)
    risk = (s.get("hallucination_risk") or 0) * 100
    lines = [
        f"幻觉风险: {risk:.0f}%（共 {total} 条声明：✅ 证实 {green} / ⚠️ 存疑 {yellow} / ❌ 证伪 {red}）",
        f"检测耗时: {data.get('elapsed_ms', 0):.0f}ms | 速度: {data.get('speed', '')} | 领域: {data.get('domain', '')}",
        "",
    ]
    for item in data.get("claims") or []:
        claim = (item or {}).get("claim") or {}
        ver = (item or {}).get("verification") or {}
        status = ver.get("status", "unverified")
        lines.append(f"{_STATUS_MARK.get(status, '⚠️')} [{status}] {claim.get('text', '')}")
        if ver.get("reason"):
            lines.append(f"   理由: {ver['reason']}")
        for src in (ver.get("sources") or [])[:2]:
            if isinstance(src, dict) and src.get("url"):
                lines.append(f"   来源: {src.get('title') or src['url']} — {src['url']}")
    quota = data.get("quota") or {}
    if quota:
        remaining = quota.get("remaining")
        lines.append(
            f"---\n额度: {quota.get('plan', '')} · 今日剩余 "
            f"{'∞' if remaining is None else remaining}"
        )
    return "\n".join(lines)


class HallucDetectTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = (self.runtime.credentials.get("api_key") or "").strip()
        if not api_key:
            raise RuntimeError(
                "HallucC API Key is missing. Configure it in the plugin settings."
            )
        text = (tool_parameters.get("text") or "").strip()
        if not text:
            raise ValueError("Parameter `text` is required")
        data = _post(
            "/detect",
            {
                "text": text,
                "speed": tool_parameters.get("speed") or "standard",
                "domain": tool_parameters.get("domain") or "general",
            },
            api_key,
        )
        yield self.create_text_message(_format(data))
        yield self.create_json_message(data)
