from sentinel.models import TokenBalance, Holdings, Flow
from sentinel import metrics

ENS_TOKEN = TokenBalance(symbol="ENS", address="0xC183", balance=10000.0, usd_value=40000.0, is_native_token=True)
USDC_TOKEN = TokenBalance(symbol="USDC", address="0xA0b", balance=5000.0, usd_value=5000.0, is_stablecoin=True)
ETH_NATIVE = TokenBalance(symbol="ETH", address="0x0", balance=10.0, usd_value=30000.0)

H = Holdings(tokens=[ENS_TOKEN, USDC_TOKEN, ETH_NATIVE])

def test_total_aum():
    assert metrics.total_aum(H) == 75000.0

def test_stable_ratio():
    assert abs(metrics.stable_ratio(H) - (5000 / 75000)) < 0.001

def test_native_concentration():
    assert abs(metrics.native_concentration(H, "ENS") - (40000 / 75000)) < 0.001

def test_eth_class_holdings():
    assert abs(metrics.eth_class_holdings(H) - (30000 / 75000)) < 0.001

def test_non_native_treasury():
    assert metrics.non_native_treasury(H, "ENS") == 35000.0

def test_runway_months_no_burn():
    result = metrics.runway_months(H, [], 30)
    assert result is None

def test_runway_months_with_burn():
    flows = [
        Flow(tx_hash="0x1", timestamp="2026-04-01", from_address="0xFe89", to_address="0xGrant",
             token_symbol="USDC", amount_usd=3500.0, direction="out")
    ]
    # Monthly burn = 3500/30*30 = 3500; liquid = 5000 (USDC) + 30000 (ETH) = 35000
    result = metrics.runway_months(H, flows, 30)
    assert result is not None
    assert abs(result - 10.0) < 0.01

def test_burn_no_outflows():
    assert metrics.burn([], 30) == 0.0

def test_empty_holdings():
    h = Holdings()
    assert metrics.total_aum(h) == 0.0
    assert metrics.stable_ratio(h) == 0.0
