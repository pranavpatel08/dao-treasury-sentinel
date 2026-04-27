---
name: dao_treasury_sentinel
description: Always-on DAO treasury analyst. Snapshots holdings, computes runway, flags concentration risk and OFAC counterparties for any Safe multisig or EOA on Ethereum.
metadata: { "openclaw": { "requires": { "bins": ["uv"], "env": ["ALCHEMY_API_KEY"] }, "homepage": "https://github.com/pranavpatel/dao-treasury-sentinel" } }
---

## When to invoke this skill

Use when the user asks about:
- Treasury health, AUM, or reserves for any DAO or multisig
- Stablecoin ratio or governance-token concentration risk
- Operating runway or burn rate
- OFAC / sanctions screening of wallet counterparties
- Risk exposure in a Safe multisig or EOA

## Example prompts → commands

| User prompt | Command |
|-------------|---------|
| "Snapshot the ENS DAO treasury" | `uv run sentinel snapshot 0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7 --native ENS` |
| "What risks does the ENS treasury have?" | `uv run sentinel risks 0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7 --native ENS` |
| "Show treasury flows for the last 30 days" | `uv run sentinel flows 0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7 --since 30d` |
| "Export ENS treasury as JSON for analysis" | `uv run sentinel snapshot 0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7 --json` |
| "Save ENS treasury report to file" | `uv run sentinel snapshot 0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7 --save report.md` |

## Output JSON schema

```json
{
  "snapshot": {
    "address": "0x...",
    "chain": "ethereum",
    "timestamp": "2026-04-26T17:00:00+00:00",
    "holdings": {
      "safe_address": "0x...",
      "total_usd": 45000000.0,
      "tokens": [
        {
          "symbol": "ENS",
          "address": "0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72",
          "balance": 500000.0,
          "usd_value": 35000000.0,
          "is_stablecoin": false,
          "is_native_token": true,
          "protocol": null
        }
      ]
    },
    "risks": [
      {
        "code": "R001_NATIVE_CONCENTRATION",
        "level": "critical",
        "description": "ENS represents 78% of treasury",
        "evidence": "$45,000,000 AUM; 78% in ENS",
        "recommendation": "Diversify into stablecoins or ETH"
      }
    ]
  },
  "metrics": {
    "total_aum": 45000000.0,
    "stable_ratio": 0.12,
    "native_concentration": 0.78,
    "eth_class": 0.08,
    "non_native_treasury": 9000000.0
  }
}
```

## Interpretation guidance

When reading output, apply these rules:
- `native_concentration > 0.5` → **CRITICAL**: Surface before all other findings. DAO is exposed to governance-token price collapse.
- `runway_months < 6` → **CRITICAL**: Flag immediately. DAO could run out of operating funds.
- `runway_months < 12` → **WARN**: Mention as upcoming concern.
- `stable_ratio < 0.05` → **WARN**: DAO is highly illiquid; vulnerable under token price stress.
- `R004_OFAC_COUNTERPARTY` → **CRITICAL**: Always surface. Recommend legal review before any further interaction with that address.
- `R005_STABLE_ISSUER_CONCENTRATION` → **WARN**: Mention USDC Circle counterparty risk if relevant.

## Dispatch

Base directory: `{baseDir}`
Entrypoint: `{baseDir}/src/sentinel/cli.py`
Install: `cd {baseDir} && uv sync`
Run: `uv run sentinel <command> <address> [options]`
