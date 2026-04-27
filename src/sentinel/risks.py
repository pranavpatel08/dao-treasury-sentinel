from sentinel.models import Holdings, Flow, Risk
from sentinel import metrics

def evaluate(
    holdings: Holdings,
    flows: list[Flow],
    sanctioned_addresses: dict[str, bool],
    native_symbol: str = "ENS",
    days: int = 30,
) -> list[Risk]:
    risks: list[Risk] = []

    # R001: native token concentration > 50%
    conc = metrics.native_concentration(holdings, native_symbol)
    if conc > 0.5:
        risks.append(Risk(
            code="R001_NATIVE_CONCENTRATION",
            level="critical",
            description=f"{native_symbol} represents {conc:.0%} of treasury",
            evidence=f"${metrics.total_aum(holdings):,.0f} AUM; {conc:.0%} in {native_symbol}",
            recommendation="Diversify into stablecoins or ETH to reduce governance-token tail risk",
        ))

    # R002: runway < 12 months
    runway = metrics.runway_months(holdings, flows, days)
    if runway is not None and runway < 12:
        risks.append(Risk(
            code="R002_RUNWAY_LOW",
            level="warn" if runway > 6 else "critical",
            description=f"Operating runway is {runway:.1f} months",
            evidence=f"Liquid assets: ${sum(t.usd_value for t in holdings.tokens if t.is_stablecoin or t.symbol == 'ETH'):,.0f}",
            recommendation="Replenish liquid reserves or reduce monthly burn rate",
        ))

    # R003: single-protocol exposure > 25%
    by_protocol: dict[str, float] = {}
    for t in holdings.tokens:
        if t.protocol:
            by_protocol[t.protocol] = by_protocol.get(t.protocol, 0) + t.usd_value
    for proto, val in by_protocol.items():
        share = val / holdings.total_usd if holdings.total_usd else 0
        if share > 0.25:
            risks.append(Risk(
                code="R003_PROTOCOL_CONCENTRATION",
                level="warn",
                description=f"{proto} exposure is {share:.0%} of treasury",
                evidence=f"${val:,.0f} held in {proto} positions",
                recommendation=f"Reduce single-protocol dependency on {proto}",
            ))

    # R004: OFAC-listed counterparty in recent flows
    for flow in flows:
        addr = flow.from_address if flow.direction == "in" else flow.to_address
        if sanctioned_addresses.get(addr.lower()):
            risks.append(Risk(
                code="R004_OFAC_COUNTERPARTY",
                level="critical",
                description=f"Transaction with OFAC-listed address {addr}",
                evidence=f"Tx: {flow.tx_hash} | Amount: ${flow.amount_usd:,.0f}",
                recommendation="Consult legal counsel; flag transaction for compliance review",
            ))
            break

    # R005: single stablecoin issuer > 50% of stablecoins
    stable_total = sum(t.usd_value for t in holdings.tokens if t.is_stablecoin)
    if stable_total > 0:
        by_stable: dict[str, float] = {}
        for t in holdings.tokens:
            if t.is_stablecoin:
                by_stable[t.symbol] = by_stable.get(t.symbol, 0) + t.usd_value
        for sym, val in by_stable.items():
            if val / stable_total > 0.5:
                risks.append(Risk(
                    code="R005_STABLE_ISSUER_CONCENTRATION",
                    level="warn",
                    description=f"{sym} is {val/stable_total:.0%} of stablecoin holdings",
                    evidence=f"${val:,.0f} of ${stable_total:,.0f} stablecoins in {sym}",
                    recommendation="Diversify stablecoins across issuers (USDC + DAI + USDT)",
                ))
                break

    return risks
