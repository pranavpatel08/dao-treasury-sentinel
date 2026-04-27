from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from sentinel.models import Report

console = Console()

def render_terminal(report: Report) -> None:
    snap = report.snapshot
    m = report.metrics

    table = Table(title=f"Treasury Snapshot: {snap.address[:10]}...")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Total AUM", f"${m.get('total_aum', 0):,.0f}")
    table.add_row("Stable Ratio", f"{m.get('stable_ratio', 0):.1%}")
    table.add_row("Native Concentration", f"{m.get('native_concentration', 0):.1%}")
    runway = m.get('runway_months')
    table.add_row("Runway", f"{runway:.1f} months" if runway else "N/A")
    console.print(table)

    if snap.risks:
        for r in snap.risks:
            color = {"info": "blue", "warn": "yellow", "critical": "red"}[r.level]
            console.print(Panel(
                f"[bold]{r.description}[/bold]\n{r.evidence}\n[dim]{r.recommendation}[/dim]",
                title=f"[{color}]{r.level.upper()}: {r.code}[/{color}]",
                border_style=color,
            ))

def render_markdown(report: Report) -> str:
    snap = report.snapshot
    m = report.metrics
    runway = m.get('runway_months')
    lines = [
        "# DAO Treasury Sentinel Report",
        f"**Address:** `{snap.address}`  ",
        f"**Chain:** {snap.chain}  ",
        f"**Timestamp:** {snap.timestamp}",
        "",
        "## Metrics",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total AUM | ${m.get('total_aum', 0):,.0f} |",
        f"| Stablecoin Ratio | {m.get('stable_ratio', 0):.1%} |",
        f"| Native Concentration | {m.get('native_concentration', 0):.1%} |",
        f"| Runway | {f'{runway:.1f} months' if runway else 'N/A'} |",
        "",
    ]
    if snap.risks:
        lines.append("## Risk Flags")
        for r in snap.risks:
            lines.append(f"- **[{r.level.upper()}] {r.code}**: {r.description}")
            lines.append(f"  - Evidence: {r.evidence}")
            lines.append(f"  - Recommendation: {r.recommendation}")
    return "\n".join(lines)

def render_json(report: Report) -> dict:
    return report.model_dump()
