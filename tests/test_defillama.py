import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sentinel.sources.defillama import get_price

USDC_ADDR = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


@pytest.mark.asyncio
async def test_get_price_returns_float():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "coins": {f"ethereum:{USDC_ADDR}": {"price": 1.0, "symbol": "USDC", "decimals": 6}}
    }
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.defillama.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        price = await get_price("ethereum", USDC_ADDR)

    assert price == 1.0


@pytest.mark.asyncio
async def test_get_price_returns_none_for_unknown():
    mock_response = MagicMock()
    mock_response.json.return_value = {"coins": {}}
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.defillama.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        price = await get_price("ethereum", "0xunknown")

    assert price is None
