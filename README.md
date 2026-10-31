# Trading-Skill

Project-level Claude Code skills for day trading, installed in `.claude/skills/`.

Source: [Jakeschincariol/day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill) v2.0.0 (commit `3d0f4ef`), MIT license (see `.claude/skills/LICENSE-day-trader-skill`).

Skills: trader-scanner, trader-news, trader-entry, trader-exit, trader-timemachine, trader-risk, trader-budget, trader-broker, trader-alerts, trader-analyst, trader-pelosi.

Notes:
- `trader-analyst` and `trader-news` need a `SEC_USER_AGENT` env var (your name and email) for SEC endpoints.
- `trader-broker` only builds order tickets; real order placement goes through a broker MCP server (e.g. Alpaca), paper trading by default.

## agiprolabs/claude-trading-skills

Also installed in `.claude/skills/`: 68 skills from [agiprolabs/claude-trading-skills](https://github.com/agiprolabs/claude-trading-skills) (commit `981e1d7`), MIT license (see `.claude/skills/LICENSE-claude-trading-skills.md`). Covers crypto/DeFi market data (CoinGecko, DexScreener, Birdeye, DefiLlama, Helius), technical analysis, backtesting, risk and position sizing, Solana/DEX execution, prediction markets and tax tools.

Notes:
- Scripts need third-party Python packages (`httpx`, `numpy`, `pandas`; some need `solders`, `pandas_ta`, `vectorbt`, `ta-lib`).
- `raptor-dex` and `jito-bundles` can sign and send real Solana transactions when given a `PRIVATE_KEY` env var or signed transactions. Use their `--demo` modes unless you mean to trade real funds.
