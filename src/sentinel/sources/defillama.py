import httpx

COINS_BASE = "https://coins.llama.fi"


async def get_price(chain: str, address: str) -> float | None:
    key = f"{chain}:{address}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{COINS_BASE}/prices/current/{key}")
        r.raise_for_status()
        data = r.json()
    coin = data.get("coins", {}).get(key)
    return float(coin["price"]) if coin and "price" in coin else None
