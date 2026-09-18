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
    passed = data.get("passed")
    lines = [
        f"{'✅ 通过' if passed else '⛔ 未通过'} | 风险等级: {data.get('risk_level', '')}"
        f" | 风险分: {data.get('risk_score', '')}",
        f"注入: {data.get('injection_detected')} | 越狱: {data.get('jailbreak_detected')}"
        f" | 有害内容: {data.get('harmful_detected')}",
    ]
    threats = data.get("threats") or []
    if threats:
        lines.append("\n命中威胁:")
        for t in threats:
            lines.append(
                f"  - [{t.get('severity', '')}] {t.get('category_name') or t.get('category', '')}"
            )
            if t.get("match_context"):
                lines.append(f"    上下文: {t['match_context']}")
            if t.get("recommendation"):
                lines.append(f"    建议: {t['recommendation']}")
    h = data.get("hallucination")
    if isinstance(h, dict):
        hs = h.get("summary") or {}
        if hs:
            risk = (hs.get("hallucination_risk") or 0) * 100
            lines.append(f"\n幻觉风险: {risk:.0f}%（存疑 {hs.get('yellow', 0)} / 证伪 {hs.get('red', 0)} / 共 {hs.get('total', 0)}）")
    quota = data.get("quota") or {}
    if quota:
        remaining = quota.get("remaining")
        lines.append(
            f"---\n额度: {quota.get('plan', '')} · 今日剩余 "
            f"{'∞' if remaining is None else remaining}"
        )
    return "\n".join(lines)


class GuardCheckTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = (self.runtime.credentials.get("api_key") or "").strip()
        if not api_key:
            raise RuntimeError(
                "HallucC API Key is missing. Configure it in the plugin settings."
            )
        output = (tool_parameters.get("output") or "").strip()
        if not output:
            raise ValueError("Parameter `output` is required")
        payload: dict[str, Any] = {
            "output": output,
            "check_hallucination": bool(tool_parameters.get("check_hallucination")),
        }
        prompt = (tool_parameters.get("prompt") or "").strip()
        if prompt:
            payload["prompt"] = prompt
        data = _post("/guard/check", payload, api_key)
        yield self.create_text_message(_format(data))
        yield self.create_json_message(data)
