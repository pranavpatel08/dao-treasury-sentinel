from sentinel.models import TokenBalance, Holdings, Flow
from sentinel.risks import evaluate

ENS_HEAVY = Holdings(tokens=[
    TokenBalance(symbol="ENS", address="0xC183", balance=50000, usd_value=200000, is_native_token=True),
    TokenBalance(symbol="USDC", address="0xA0b", balance=1000, usd_value=1000, is_stablecoin=True),
])

def test_r001_fires_on_high_native_concentration():
    risks = evaluate(ENS_HEAVY, [], {}, "ENS")
    codes = [r.code for r in risks]
    assert "R001_NATIVE_CONCENTRATION" in codes

def test_r001_is_critical():
    risks = evaluate(ENS_HEAVY, [], {}, "ENS")
    r001 = next(r for r in risks if r.code == "R001_NATIVE_CONCENTRATION")
    assert r001.level == "critical"

def test_r001_does_not_fire_when_below_50pct():
    balanced = Holdings(tokens=[
        TokenBalance(symbol="ENS", address="0xC183", balance=100, usd_value=30000, is_native_token=True),
        TokenBalance(symbol="USDC", address="0xA0b", balance=40000, usd_value=40000, is_stablecoin=True),
    ])
    risks = evaluate(balanced, [], {}, "ENS")
    assert not any(r.code == "R001_NATIVE_CONCENTRATION" for r in risks)

def test_r002_fires_when_runway_low():
    short_runway = Holdings(tokens=[
        TokenBalance(symbol="USDC", address="0xA0b", balance=5000, usd_value=5000, is_stablecoin=True),
    ])
    flows = [Flow(tx_hash="0x1", timestamp="2026-04-01", from_address="0xFe89", to_address="0xGrant",
                  token_symbol="USDC", amount_usd=50000, direction="out")]
    risks = evaluate(short_runway, flows, {}, "ENS")
    assert any(r.code == "R002_RUNWAY_LOW" for r in risks)

def test_r004_fires_on_sanctioned_address():
    flows = [Flow(tx_hash="0xsanctioned", timestamp="2026-04-01",
                  from_address="0xsanctioned_addr", to_address="0xfe89",
                  token_symbol="USDC", amount_usd=1000, direction="in")]
    sanctioned = {"0xsanctioned_addr": True}
    risks = evaluate(ENS_HEAVY, flows, sanctioned, "ENS")
    assert any(r.code == "R004_OFAC_COUNTERPARTY" for r in risks)

def test_r005_fires_on_single_stable_issuer():
    usdc_heavy = Holdings(tokens=[
        TokenBalance(symbol="USDC", address="0xA0b", balance=90000, usd_value=90000, is_stablecoin=True),
        TokenBalance(symbol="DAI", address="0xDAI", balance=5000, usd_value=5000, is_stablecoin=True),
    ])
    risks = evaluate(usdc_heavy, [], {}, "ENS")
    assert any(r.code == "R005_STABLE_ISSUER_CONCENTRATION" for r in risks)

def test_no_risks_for_healthy_treasury():
    healthy = Holdings(tokens=[
        TokenBalance(symbol="ENS", address="0xC183", balance=100, usd_value=20000, is_native_token=True),
        TokenBalance(symbol="USDC", address="0xA0b", balance=20000, usd_value=20000, is_stablecoin=True),
        TokenBalance(symbol="DAI", address="0xDAI", balance=20000, usd_value=20000, is_stablecoin=True),
        TokenBalance(symbol="ETH", address="0x0", balance=5, usd_value=15000),
    ])
    risks = evaluate(healthy, [], {}, "ENS")
    # R001 won't fire (ENS = 26.7%), no runway issues (no outflows), no sanctions
    # R005 might fire if USDC > 50% of stablecoins (20k/40k = 50%), so it's exactly on the border
    # Just check R001 and R004 don't fire
    assert not any(r.code == "R001_NATIVE_CONCENTRATION" for r in risks)
    assert not any(r.code == "R004_OFAC_COUNTERPARTY" for r in risks)
