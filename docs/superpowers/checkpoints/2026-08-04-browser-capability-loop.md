# Browser Capability Loop Checkpoint

- Branch: `feat/browser-capability-loop`
- Added regression coverage for implementation-agent edit+execute and browser tool ownership.
- `implementation-agent` now owns the direct browser-driven change loop.
- `browser-agent` remains read-only and is scoped to independent browser validation.
- `orchestrator` routes web/UI fixes directly to `implementation-agent` and reuses writer browser evidence when sufficient.
- `scripts/validate_agents.py` explicitly allowlists `implementation-agent` for the narrow edit+execute runtime loop.
- Final repository validation is expected from GitHub Actions because the current execution sandbox cannot resolve github.com for a local clone.
