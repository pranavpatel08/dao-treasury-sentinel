import httpx
from typing import Any


async def _rpc(method: str, params: list, api_key: str) -> Any:
    url = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"Alchemy RPC error: {data['error']}")
        return data.get("result")


async def get_asset_transfers(address: str, api_key: str, days: int = 90) -> list[dict]:
    params = [{
        "toAddress": address,
        "category": ["external", "erc20"],
        "maxCount": "0x32",
        "withMetadata": True,
    }]
    result = await _rpc("alchemy_getAssetTransfers", params, api_key)
    return result.get("transfers", []) if result else []


async def eth_call(to: str, data: str, api_key: str) -> str:
    result = await _rpc("eth_call", [{"to": to, "data": data}, "latest"], api_key)
    return result or "0x"
