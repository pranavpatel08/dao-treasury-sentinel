import asyncio
import json
import os
from datetime import datetime, timezone

import httpx
import typer
from rich.console import Console

from sentinel import metrics
from sentinel.models import Flow, Holdings, Report, Snapshot, TokenBalance
from sentinel.report import render_json, render_markdown, render_terminal
from sentinel.risks import evaluate
from sentinel.sources.alchemy import (
    get_asset_transfers,
    get_token_balances,
    get_token_metadata,
)
from sentinel.sources.defillama import get_price
from sentinel.sources.sanctions import is_sanctioned

app = typer.Typer(help="DAO Treasury Sentinel — always-on treasury analyst for any Safe multisig")
console = Console()

STABLECOINS = {"USDC", "USDT", "DAI", "FRAX", "crvUSD", "LUSD", "GUSD", "BUSD", "TUSD"}
ETH_ADDRESS = "0x0000000000000000000000000000000000000000"


def _get_api_key() -> str:
    key = os.getenv("ALCHEMY_API_KEY")
    if not key:
        typer.echo("Error: ALCHEMY_API_KEY env var not set", err=True)
        raise typer.Exit(1)
    return key


async def _rpc_raw(method: str, params: list, api_key: str) -> str | None:
    url = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    return data.get("result")


async def _fetch_holdings(address: str, native_symbol: str, api_key: str) -> Holdings:
    """Fetch token balances via Alchemy + price via DefiLlama."""
    tokens: list[TokenBalance] = []

    # Fetch ETH balance via eth_getBalance
    eth_balance_result = await _rpc_raw("eth_getBalance", [address, "latest"], api_key)
    if eth_balance_result:
        eth_wei = int(eth_balance_result, 16)
        eth_amount = eth_wei / 1e18
        eth_price = await get_price("ethereum", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
        eth_usd = eth_amount * (eth_price or 0)
        if eth_usd > 100:
            tokens.append(TokenBalance(
                symbol="ETH",
                address=ETH_ADDRESS,
                balance=eth_amount,
                usd_value=eth_usd,
            ))

    # Fetch ERC-20 balances
    raw_balances = await get_token_balances(address, api_key)
    for item in raw_balances[:50]:  # cap at 50 tokens
        contract = item["contractAddress"]
        hex_bal = item["tokenBalance"]
        try:
            raw_amount = int(hex_bal, 16)
        except (ValueError, TypeError):
            continue
        if raw_amount == 0:
            continue

        meta = await get_token_metadata(contract, api_key)
        symbol = meta.get("symbol", "UNKNOWN")
        decimals = meta.get("decimals", 18) or 18
        amount = raw_amount / (10 ** decimals)

        price = await get_price("ethereum", contract)
        if price is None:
            continue  # skip unpriced tokens
        usd_value = amount * price
        if usd_value < 100:
            continue  # skip dust

        tokens.append(TokenBalance(
            symbol=symbol,
            address=contract,
            balance=amount,
            usd_value=usd_value,
            is_stablecoin=symbol in STABLECOINS,
            is_native_token=(symbol == native_symbol),
        ))

    return Holdings(safe_address=address, tokens=tokens)


@app.command()
def snapshot(
    address: str = typer.Argument(..., help="Safe multisig or EOA address (0x...)"),
    native: str = typer.Option("ENS", "--native", help="Native governance token symbol"),
    output_json: bool = typer.Option(False, "--json", help="Output JSON instead of Rich terminal"),
    save: str = typer.Option(None, "--save", help="Save Markdown report to file path"),
):
    """Snapshot treasury holdings and compute metrics."""
    api_key = _get_api_key()
    asyncio.run(_do_snapshot(address, native, api_key, output_json, save))


async def _do_snapshot(address: str, native: str, api_key: str, output_json: bool, save: str | None) -> None:
    with console.status("[bold green]Fetching holdings via Alchemy + DefiLlama..."):
        holdings = await _fetch_holdings(address, native, api_key)

    m = {
        "total_aum": metrics.total_aum(holdings),
        "stable_ratio": metrics.stable_ratio(holdings),
        "native_concentration": metrics.native_concentration(holdings, native),
        "eth_class": metrics.eth_class_holdings(holdings),
        "non_native_treasury": metrics.non_native_treasury(holdings, native),
    }

    snap = Snapshot(
        address=address,
        timestamp=datetime.now(timezone.utc).isoformat(),
        holdings=holdings,
    )
    report = Report(snapshot=snap, metrics=m)

    if output_json:
        print(json.dumps(render_json(report), indent=2))
    else:
        render_terminal(report)

    if save:
        with open(save, "w") as f:
            f.write(render_markdown(report))
        console.print(f"[green]Saved to {save}[/green]")


@app.command()
def risks(
    address: str = typer.Argument(..., help="Safe multisig address (0x...)"),
    native: str = typer.Option("ENS", "--native", help="Native governance token symbol"),
):
    """Evaluate risk flags for a treasury."""
    api_key = _get_api_key()
    asyncio.run(_do_risks(address, native, api_key))


async def _do_risks(address: str, native: str, api_key: str) -> None:
    with console.status("[bold yellow]Analyzing risks..."):
        holdings = await _fetch_holdings(address, native, api_key)
        # Fetch recent flows for runway calculation
        raw_transfers = await get_asset_transfers(address, api_key, days=30)
        flows = _parse_flows(raw_transfers, address)
        # Screen top counterparties
        counterparties = {f.from_address for f in flows if f.direction == "in"} | \
                         {f.to_address for f in flows if f.direction == "out"}
        sanctioned = {}
        for addr in list(counterparties)[:20]:  # screen top 20
            try:
                sanctioned[addr.lower()] = await is_sanctioned(addr, api_key)
            except Exception:
                pass
        risk_list = evaluate(holdings, flows, sanctioned, native)

    if not risk_list:
        console.print("[green]No risk flags detected[/green]")
        return

    snap = Snapshot(address=address, timestamp="", holdings=holdings, risks=risk_list)
    render_terminal(Report(snapshot=snap, metrics={
        "total_aum": metrics.total_aum(holdings),
        "stable_ratio": metrics.stable_ratio(holdings),
        "native_concentration": metrics.native_concentration(holdings, native),
    }))


@app.command()
def flows(
    address: str = typer.Argument(..., help="Safe multisig address (0x...)"),
    since: str = typer.Option("30d", "--since", help="Lookback window (e.g. 30d, 90d)"),
):
    """Show recent treasury flows."""
    api_key = _get_api_key()
    days = int(since.rstrip("d"))
    asyncio.run(_do_flows(address, api_key, days))


async def _do_flows(address: str, api_key: str, days: int) -> None:
    from rich.table import Table
    with console.status(f"[bold]Fetching {days}d flows..."):
        raw = await get_asset_transfers(address, api_key, days=days)
        flow_list = _parse_flows(raw, address)

    if not flow_list:
        console.print("[dim]No flows found[/dim]")
        return

    table = Table(title=f"Treasury Flows (last {days}d)")
    table.add_column("Date", style="dim")
    table.add_column("Direction", style="bold")
    table.add_column("Token", style="cyan")
    table.add_column("USD", justify="right")
    for f in flow_list[:25]:
        color = "green" if f.direction == "in" else "red"
        table.add_row(
            f.timestamp[:10],
            f"[{color}]{f.direction.upper()}[/{color}]",
            f.token_symbol,
            f"${f.amount_usd:,.0f}",
        )
    console.print(table)


def _parse_flows(raw_transfers: list[dict], address: str) -> list[Flow]:
    flow_list = []
    for t in raw_transfers:
        to_addr = (t.get("to") or "").lower()
        from_addr = (t.get("from") or "").lower()
        direction = "in" if to_addr == address.lower() else "out"
        try:
            amount_usd = float(t.get("value") or 0)
        except (TypeError, ValueError):
            amount_usd = 0.0
        flow_list.append(Flow(
            tx_hash=t.get("hash", ""),
            timestamp=t.get("metadata", {}).get("blockTimestamp", ""),
            from_address=from_addr,
            to_address=to_addr,
            token_symbol=t.get("asset") or "ETH",
            amount_usd=amount_usd,
            direction=direction,
        ))
    return flow_list


if __name__ == "__main__":
    app()
