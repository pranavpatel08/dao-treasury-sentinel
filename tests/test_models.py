from sentinel.models import TokenBalance, Holdings, Flow, Risk, Snapshot, Report

def test_token_balance_usd():
    tb = TokenBalance(symbol="USDC", address="0xA0b", balance=1000.0, usd_value=1000.0)
    assert tb.usd_value == 1000.0

def test_holdings_total_usd():
    h = Holdings(tokens=[
        TokenBalance(symbol="ETH", address="0x0", balance=1.0, usd_value=3000.0),
        TokenBalance(symbol="USDC", address="0xA0b", balance=1000.0, usd_value=1000.0),
    ])
    assert h.total_usd == 4000.0

def test_holdings_empty_total():
    h = Holdings()
    assert h.total_usd == 0.0

def test_flow_direction():
    f = Flow(tx_hash="0x1", timestamp="2026-01-01", from_address="0xA", to_address="0xB",
             token_symbol="USDC", amount_usd=100.0, direction="out")
    assert f.direction == "out"

def test_risk_levels():
    r = Risk(code="R001", level="critical", description="test", evidence="ev", recommendation="rec")
    assert r.level == "critical"
