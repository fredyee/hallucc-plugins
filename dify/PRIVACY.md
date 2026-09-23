# Privacy Policy — HallucC Dify Plugin

## What this plugin does

This plugin is a thin API client. It forwards the content you explicitly pass to each
tool (text to verify, agent trajectories, AI outputs to safety-check, CUA action
lists, or Agent source code) to the HallucC cloud API at `https://aihcc.cloud/api`,
and returns the API response to your Dify workflow. No detection, model, or search
logic runs inside the plugin.

## Data sent to HallucC

- Your HallucC API key (used only for `Authorization` header authentication).
- The exact tool parameters you provide: text, trajectory JSON, guard output/prompt,
  CUA action JSON, or source code text.

Nothing else is collected: no telemetry, no analytics, no Dify workspace data, no
environment scraping.

## How HallucC handles your data (service side)

- Submitted text is processed to perform detection and is **desensitized (PII
  redaction) before any persistence**; original submitted text is not stored in raw
  form.
- Detection metadata (risk scores, claim statuses) is retained to provide history,
  quota accounting, and result sharing features visible in your own account.
- Data is not sold or shared with third parties beyond the infrastructure providers
  required to operate the service (cloud hosting, LLM and search API providers needed
  to perform verification).

## Data stored inside Dify

Only your API key, stored by Dify's own credential mechanism. The plugin itself
persists nothing.

## Contact

Questions: <https://aihcc.cloud> · service operator: HallucC (fredyee).
