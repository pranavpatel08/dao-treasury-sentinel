from pydantic import BaseModel, computed_field
from typing import Literal

class TokenBalance(BaseModel):
    symbol: str
    address: str
    balance: float
    usd_value: float
    is_stablecoin: bool = False
    is_native_token: bool = False
    protocol: str | None = None

class Holdings(BaseModel):
    safe_address: str = ""
    tokens: list[TokenBalance] = []

    @computed_field
    @property
    def total_usd(self) -> float:
        return sum(t.usd_value for t in self.tokens)

class Flow(BaseModel):
    tx_hash: str
    timestamp: str
    from_address: str
    to_address: str
    token_symbol: str
    amount_usd: float
    direction: Literal["in", "out"]

class Risk(BaseModel):
    code: str
    level: Literal["info", "warn", "critical"]
    description: str
    evidence: str
    recommendation: str

class Snapshot(BaseModel):
    address: str
    chain: str = "ethereum"
    timestamp: str
    holdings: Holdings
    flows_30d: list[Flow] = []
    risks: list[Risk] = []

class Report(BaseModel):
    snapshot: Snapshot
    metrics: dict[str, float] = {}
