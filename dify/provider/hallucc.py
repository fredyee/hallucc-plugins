from typing import Any

import requests

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

API_BASE = "https://aihcc.cloud/api"


class HalluccProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        api_key = (credentials.get("api_key") or "").strip()
        if not api_key:
            raise ToolProviderCredentialValidationError(
                "HallucC API Key is required. Create one at https://aihcc.cloud/keys"
            )
        # /cua/classify is free and consumes no quota — safe validation probe.
        try:
            resp = requests.post(
                f"{API_BASE}/cua/classify",
                json={"actions": [{"action": "click", "x": 1, "y": 1}]},
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
        except requests.RequestException as e:
            raise ToolProviderCredentialValidationError(
                f"Cannot reach HallucC API: {e}"
            )
        if resp.status_code in (401, 403):
            raise ToolProviderCredentialValidationError(
                "Invalid HallucC API Key. Create one at https://aihcc.cloud/keys"
            )
