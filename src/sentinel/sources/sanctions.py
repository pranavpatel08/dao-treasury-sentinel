from sentinel.sources.alchemy import eth_call

ORACLE = "0x40C57923924B5c5c5455c48D93317139ADDaC8fb"


def _encode_is_sanctioned(address: str) -> str:
    # keccak256("isSanctioned(address)")[:4] = 0xb021612a
    selector = "b021612a"
    padded = address.lower().replace("0x", "").zfill(64)
    return f"0x{selector}{padded}"


async def is_sanctioned(address: str, api_key: str) -> bool:
    data = _encode_is_sanctioned(address)
    result = await eth_call(ORACLE, data, api_key)
    # 32-byte bool: "0x0...01" means sanctioned, "0x0...00" means clean
    return result.strip() not in ("0x", "0x" + "0" * 64, "0x0000000000000000000000000000000000000000000000000000000000000000")
