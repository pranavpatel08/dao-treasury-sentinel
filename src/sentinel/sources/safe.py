import httpx
from typing import Any

BASE = "https://safe-transaction-mainnet.safe.global/api/v1"


async def get_balances_usd(safe: str) -> list[dict[str, Any]]:
    """Return token balances for a Gnosis Safe, with human-readable amounts and USD values."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{BASE}/safes/{safe}/balances/",
            params={"trusted": "False", "exclude_spam": "True"},
        )
        r.raise_for_status()
        raw = r.json()

    out = []
    for item in raw:
        token = item.get("token") or {}
        decimals = token.get("decimals", 18) if token else 18
        symbol = token.get("symbol", "ETH") if token else "ETH"
        address = item.get("tokenAddress") or "0x0"
        balance_raw = float(item.get("balance", 0))
        usd_value = float(item.get("fiatBalance", 0))
        out.append({
            "symbol": symbol,
            "address": address,
            "balance": balance_raw / (10 ** decimals),
            "usd_value": usd_value,
        })
    return out


async def get_safe_info(safe: str) -> dict[str, Any]:
    """Return metadata about a Gnosis Safe (owners, threshold, version, etc.)."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/safes/{safe}/")
        r.raise_for_status()
        return r.json()


async def get_transfers(safe: str, limit: int = 100) -> list[dict[str, Any]]:
    """Return the most recent token/ETH transfers for a Gnosis Safe."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{BASE}/safes/{safe}/transfers/",
            params={"limit": limit},
        )
        r.raise_for_status()
        return r.json().get("results", [])
