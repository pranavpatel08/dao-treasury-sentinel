# DAO Treasury Sentinel

> **Always-on treasury analyst for any DAO — free, open-source, OpenClaw-native.**

---

## Track

**Allocation (分配)**

---

## TL;DR

DAOs collectively hold over $32 billion on-chain, with ~80% concentrated in their own governance tokens. Premium treasury management firms charge $322K–$2.5M/year. Below that price tier, DAOs run on manual spreadsheets and react to depegs hours too late. DAO Treasury Sentinel is a free, MIT-licensed OpenClaw skill that gives any DAO an always-on treasury analyst: one command snapshots holdings, computes runway, and flags critical risks — no subscriptions, no vendor lock-in, works with any Ethereum Safe multisig or EOA.

---

## Problem

DAOs face a structural treasury intelligence gap:

- **Concentration risk**: 80% of DAO treasury value sits in governance tokens. When those tokens drop 50%, the operating runway collapses simultaneously.
- **Slow depeg response**: The ENS DAO held USDC during the March 2023 Silicon Valley Bank depeg, losing purchasing power before governance could react.
- **Sanctions exposure**: DAOs with grant programs receive funds from thousands of addresses — no tooling exists to flag OFAC-listed counterparties.
- **Price tier gap**: Karpatkey, Llama, and Steakhouse charge $322K–$2.5M/year for treasury intelligence. Smaller DAOs have nothing.

---

## Solution & Technical Implementation

DAO Treasury Sentinel is a Python CLI tool packaged as an OpenClaw skill. One command produces a complete treasury health report.

### Architecture

```
ALCHEMY API ──────────────────────────────────┐
  alchemy_getTokenBalances                     │
  alchemy_getTokenMetadata                     ├──► Normalize Holdings
  alchemy_getAssetTransfers                    │
DEFILLAMA (free coins API) ───────────────────┘

Holdings + Flows ─► Metrics ─► Risk Engine ─► Report
                                   │               │
                    Chainalysis Oracle          Rich Terminal
                    (on-chain OFAC)             Markdown File
                                               JSON Sidecar
```

### Commands

```bash
# Snapshot any Safe multisig
sentinel snapshot 0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7 --native ENS

# Evaluate risk flags
sentinel risks 0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7

# Show 30-day flows
sentinel flows 0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7 --since 30d

# Export JSON for downstream agents
sentinel snapshot 0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7 --json
```

### Example output (ENS DAO, April 2026)

```
       Treasury Snapshot: 0xFe89cc7a...
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric               ┃       Value ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ Total AUM            │ $76,381,675 │
│ Stable Ratio         │        6.8% │
│ Native Concentration │       79.2% │
│ Runway               │         N/A │
└──────────────────────┴─────────────┘
╭──────────────── CRITICAL: R001_NATIVE_CONCENTRATION ─────────────────╮
│ ENS represents 79% of treasury                                       │
│ $76,381,675 AUM; 79% in ENS                                          │
│ Diversify into stablecoins or ETH to reduce governance-token risk    │
╰──────────────────────────────────────────────────────────────────────╯
╭──────────────── WARN: R005_STABLE_ISSUER_CONCENTRATION ──────────────╮
│ USDC is 100% of stablecoin holdings                                  │
│ $5,199,900 of $5,199,900 stablecoins in USDC                         │
│ Diversify stablecoins across issuers (USDC + DAI + USDT)            │
╰──────────────────────────────────────────────────────────────────────╯
```

### 5 Risk Flags

| Code | Trigger | Level |
|------|---------|-------|
| R001_NATIVE_CONCENTRATION | Governance token > 50% AUM | Critical |
| R002_RUNWAY_LOW | Operating runway < 12 months | Warn/Critical |
| R003_PROTOCOL_CONCENTRATION | Single protocol > 25% AUM | Warn |
| R004_OFAC_COUNTERPARTY | OFAC-listed address in flows | Critical |
| R005_STABLE_ISSUER_CONCENTRATION | Single stablecoin > 50% of stables | Warn |

---

## Repo

https://github.com/pranavpatel08/dao-treasury-sentinel

---


## Public Goods Statement

- **MIT licensed** — fork, extend, deploy without restrictions
- **DAO-agnostic** — works for any Safe multisig or EOA on Ethereum
- **All data sources free**: Alchemy free tier (30M CU/month), DefiLlama coins API (no key), Chainalysis on-chain oracle (no account needed)
- **No vendor lock-in** — swap RPC providers by changing one env var
- **Designed for fork-and-extend** — add chains, metrics, risk flags, or webhook alerts as your DAO needs them

---

## Risks & Dependencies

| Risk | Mitigation |
|------|-----------|
| Alchemy free-tier rate limits during live demo | Pre-committed example output in `examples/` works offline |
| Safe API authentication requirement (endpoint moved) | Pivoted to Alchemy `getTokenBalances` + DefiLlama pricing |
| DefiLlama Pro-only treasury endpoint | Used only the free `coins.llama.fi` API |
| Chainalysis oracle staleness | On-chain oracle is updated in real time by Chainalysis |
| Single-chain MVP | Multi-chain (Optimism, Arbitrum) in roadmap |

---

## Roadmap

1. **Multi-chain**: Optimism, Arbitrum, Base (Etherscan V2 + Safe TX Service per-chain)
2. **Natural language Q&A**: "Which grants haven't deployed funds?"
3. **Alert webhooks**: Slack/Discord notifications on risk flag changes
4. **Position-level P&L**: DeFi yield positions tracked via DefiLlama protocol API

---

## Contact

**Email:** patel.pranav2@northeastern.edu

**Payout address (Ethereum mainnet):** `0x950739a11ba0820ceEfFFEC4682ec352058deE2d`

---

## Setup

```bash
# Install (requires uv)
git clone https://github.com/pranavpatel08/dao-treasury-sentinel
cd dao-treasury-sentinel
uv sync

# Configure
cp .env.example .env
# Edit .env: set ALCHEMY_API_KEY=your_key

# Run
uv run sentinel snapshot 0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7 --native ENS
```

*One env var. One command. Full treasury picture.*
