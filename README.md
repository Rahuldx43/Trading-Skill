# Trading-Skill

Project-level Claude Code skills for day trading, installed in `.claude/skills/`.

Source: [Jakeschincariol/day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill) v2.0.0 (commit `3d0f4ef`), MIT license (see `.claude/skills/LICENSE-day-trader-skill`).

Skills: trader-scanner, trader-news, trader-entry, trader-exit, trader-timemachine, trader-risk, trader-budget, trader-broker, trader-alerts, trader-analyst, trader-pelosi.

Notes:
- `trader-analyst` and `trader-news` need a `SEC_USER_AGENT` env var (your name and email) for SEC endpoints.
- `trader-broker` only builds order tickets; real order placement goes through a broker MCP server (e.g. Alpaca), paper trading by default.
