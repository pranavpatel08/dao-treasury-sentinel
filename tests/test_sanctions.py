import pytest
from unittest.mock import AsyncMock, patch
from sentinel.sources.sanctions import is_sanctioned


@pytest.mark.asyncio
async def test_clean_address_not_sanctioned():
    with patch("sentinel.sources.sanctions.eth_call", new=AsyncMock(
        return_value="0x0000000000000000000000000000000000000000000000000000000000000000"
    )):
        result = await is_sanctioned("0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7", api_key="fake")
    assert result is False


@pytest.mark.asyncio
async def test_sanctioned_address_detected():
    with patch("sentinel.sources.sanctions.eth_call", new=AsyncMock(
        return_value="0x0000000000000000000000000000000000000000000000000000000000000001"
    )):
        result = await is_sanctioned("0xdeadbeef000000000000000000000000deadbeef", api_key="fake")
    assert result is True
