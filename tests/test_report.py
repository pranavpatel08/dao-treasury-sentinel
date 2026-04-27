import json
from sentinel.models import TokenBalance, Holdings, Risk, Snapshot, Report
from sentinel.report import render_markdown, render_json

SNAP = Snapshot(
    address="0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7",
    timestamp="2026-04-26T17:00:00Z",
    holdings=Holdings(tokens=[
        TokenBalance(symbol="USDC", address="0xA0b", balance=1000, usd_value=1000.0, is_stablecoin=True),
        TokenBalance(symbol="ENS", address="0xC183", balance=5000, usd_value=20000.0, is_native_token=True),
    ]),
    risks=[
        Risk(code="R001_NATIVE_CONCENTRATION", level="critical",
             description="ENS is 95% of treasury", evidence="$21,000 AUM",
             recommendation="Diversify")
    ]
)
R = Report(snapshot=SNAP, metrics={"total_aum": 21000.0, "stable_ratio": 0.048, "native_concentration": 0.952})

def test_render_markdown_contains_address():
    md = render_markdown(R)
    assert "0xFe89" in md

def test_render_markdown_contains_metrics():
    md = render_markdown(R)
    assert "21,000" in md
    assert "4.8%" in md

def test_render_markdown_contains_risks():
    md = render_markdown(R)
    assert "R001_NATIVE_CONCENTRATION" in md
    assert "CRITICAL" in md

def test_render_json_valid_structure():
    d = render_json(R)
    assert d["snapshot"]["address"] == "0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7"
    assert isinstance(d["metrics"]["total_aum"], float)
    assert d["metrics"]["total_aum"] == 21000.0

def test_render_json_risks_present():
    d = render_json(R)
    risks = d["snapshot"]["risks"]
    assert len(risks) == 1
    assert risks[0]["code"] == "R001_NATIVE_CONCENTRATION"
    assert risks[0]["level"] == "critical"

def test_render_json_serializable():
    d = render_json(R)
    # Must be JSON-serializable
    json.dumps(d)
