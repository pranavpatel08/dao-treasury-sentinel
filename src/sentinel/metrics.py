from sentinel.models import Holdings, Flow

def total_aum(h: Holdings) -> float:
    return h.total_usd

def stable_ratio(h: Holdings) -> float:
    stable = sum(t.usd_value for t in h.tokens if t.is_stablecoin)
    return stable / h.total_usd if h.total_usd else 0.0

def native_concentration(h: Holdings, native_symbol: str) -> float:
    native = sum(t.usd_value for t in h.tokens if t.symbol == native_symbol)
    return native / h.total_usd if h.total_usd else 0.0

def eth_class_holdings(h: Holdings) -> float:
    eth_syms = {"ETH", "WETH", "stETH", "wstETH", "rETH"}
    total = sum(t.usd_value for t in h.tokens if t.symbol in eth_syms)
    return total / h.total_usd if h.total_usd else 0.0

def non_native_treasury(h: Holdings, native_symbol: str) -> float:
    return sum(t.usd_value for t in h.tokens if t.symbol != native_symbol)

def burn(flows: list[Flow], days: int) -> float:
    outflows = [f.amount_usd for f in flows if f.direction == "out"]
    if not outflows:
        return 0.0
    return sum(outflows) / days * 30  # normalize to monthly

def runway_months(h: Holdings, flows: list[Flow], days: int) -> float | None:
    monthly_burn = burn(flows, days)
    if monthly_burn <= 0:
        return None
    liquid = sum(t.usd_value for t in h.tokens if t.is_stablecoin or t.symbol == "ETH")
    return liquid / monthly_burn
