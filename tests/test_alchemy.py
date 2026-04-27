import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from sentinel.sources.alchemy import get_asset_transfers, eth_call

FIXTURE = json.loads(Path("tests/fixtures/alchemy_transfers.json").read_text())


@pytest.mark.asyncio
async def test_get_asset_transfers_returns_list():
    mock_response = MagicMock()
    mock_response.json.return_value = FIXTURE
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.alchemy.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await get_asset_transfers("0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7", api_key="fake")

    assert isinstance(result, list)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_eth_call_returns_string():
    mock_response = MagicMock()
    mock_response.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": "0x0000000000000000000000000000000000000000000000000000000000000000"}
    mock_response.raise_for_status.return_value = None

    with patch("sentinel.sources.alchemy.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await eth_call("0x40C57923924B5c5c5455c48D93317139ADDaC8fb", "0xb021612a" + "0" * 64, api_key="fake")

    assert isinstance(result, str)
    assert result.startswith("0x")
