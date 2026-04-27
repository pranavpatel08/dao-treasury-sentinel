import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from sentinel.sources.safe import get_balances_usd, get_safe_info, get_transfers

FIXTURE_DIR = Path(__file__).parent / "fixtures"
BALANCES_FIXTURE = json.loads((FIXTURE_DIR / "safe_balances.json").read_text())
SAFE_INFO_FIXTURE = json.loads((FIXTURE_DIR / "safe_info.json").read_text())

ENS_SAFE = "0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7"


# ---------------------------------------------------------------------------
# get_balances_usd
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_balances_returns_list():
    mock_response = MagicMock()
    mock_response.json.return_value = BALANCES_FIXTURE
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await get_balances_usd(ENS_SAFE)

    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_get_balances_required_fields():
    """Every item must have symbol, address, balance, usd_value."""
    mock_response = MagicMock()
    mock_response.json.return_value = BALANCES_FIXTURE
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await get_balances_usd(ENS_SAFE)

    for item in result:
        assert "symbol" in item
        assert "address" in item
        assert "balance" in item
        assert "usd_value" in item
        assert isinstance(item["usd_value"], float)
        assert isinstance(item["balance"], float)


@pytest.mark.asyncio
async def test_get_balances_eth_entry():
    """ETH (null tokenAddress) is parsed correctly."""
    mock_response = MagicMock()
    mock_response.json.return_value = BALANCES_FIXTURE
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await get_balances_usd(ENS_SAFE)

    eth = next((r for r in result if r["symbol"] == "ETH"), None)
    assert eth is not None, "Expected an ETH entry"
    assert eth["address"] == "0x0"
    assert eth["balance"] > 0


@pytest.mark.asyncio
async def test_get_balances_erc20_decimals():
    """USDC (6 decimals) balance should be divided correctly."""
    mock_response = MagicMock()
    mock_response.json.return_value = BALANCES_FIXTURE
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await get_balances_usd(ENS_SAFE)

    usdc = next((r for r in result if r["symbol"] == "USDC"), None)
    assert usdc is not None, "Expected a USDC entry"
    # raw balance 5200000000000 / 10^6 = 5_200_000.0
    assert usdc["balance"] == pytest.approx(5_200_000.0)


@pytest.mark.asyncio
async def test_get_balances_ens_token():
    """ENS token (18 decimals) appears in results."""
    mock_response = MagicMock()
    mock_response.json.return_value = BALANCES_FIXTURE
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await get_balances_usd(ENS_SAFE)

    ens = next((r for r in result if r["symbol"] == "ENS"), None)
    assert ens is not None, "Expected an ENS entry"
    # raw balance 52000000000000000000000000 / 10^18 = 52_000_000.0
    assert ens["balance"] == pytest.approx(52_000_000.0)
    assert ens["usd_value"] == pytest.approx(104_000_000.0)


@pytest.mark.asyncio
async def test_get_balances_empty_response():
    """Empty list from API should return empty list."""
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await get_balances_usd(ENS_SAFE)

    assert result == []


@pytest.mark.asyncio
async def test_get_balances_raises_on_http_error():
    """HTTP errors propagate to the caller."""
    import httpx

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "403 Forbidden", request=MagicMock(), response=MagicMock()
    )

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        with pytest.raises(httpx.HTTPStatusError):
            await get_balances_usd(ENS_SAFE)


# ---------------------------------------------------------------------------
# get_safe_info
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_safe_info_returns_dict():
    mock_response = MagicMock()
    mock_response.json.return_value = SAFE_INFO_FIXTURE
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await get_safe_info(ENS_SAFE)

    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_get_safe_info_has_owners_and_threshold():
    mock_response = MagicMock()
    mock_response.json.return_value = SAFE_INFO_FIXTURE
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await get_safe_info(ENS_SAFE)

    assert "owners" in result
    assert "threshold" in result
    assert isinstance(result["owners"], list)
    assert result["threshold"] == 4
    assert len(result["owners"]) == 5


# ---------------------------------------------------------------------------
# get_transfers
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_transfers_returns_list():
    transfers_fixture = {"count": 0, "next": None, "previous": None, "results": []}
    mock_response = MagicMock()
    mock_response.json.return_value = transfers_fixture
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await get_transfers(ENS_SAFE)

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_transfers_default_limit():
    """get_transfers passes limit=100 by default."""
    transfers_fixture = {"count": 0, "next": None, "previous": None, "results": []}
    mock_response = MagicMock()
    mock_response.json.return_value = transfers_fixture
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.get = mock_get
        await get_transfers(ENS_SAFE)

    _, kwargs = mock_get.call_args
    assert kwargs.get("params", {}).get("limit") == 100


@pytest.mark.asyncio
async def test_get_transfers_custom_limit():
    """get_transfers respects custom limit parameter."""
    transfers_fixture = {"count": 0, "next": None, "previous": None, "results": []}
    mock_response = MagicMock()
    mock_response.json.return_value = transfers_fixture
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.safe.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.get = mock_get
        await get_transfers(ENS_SAFE, limit=50)

    _, kwargs = mock_get.call_args
    assert kwargs.get("params", {}).get("limit") == 50
