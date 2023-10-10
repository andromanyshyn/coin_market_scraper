import asyncio
import json

import pytest
from unittest.mock import Mock, patch, AsyncMock
from markets.binance import BinanceWebSocket


# Define a mock database for testing
@pytest.fixture
def mock_db():
    return {}


sample_data = [{"s": "BTCUSDT", "a": 45000.00, "b": 44950.00}, {"s": "ETHUSDT", "a": 3000.00, "b": 2995.00}]


@pytest.fixture
async def mock_websockets_connect():
    with patch('websockets.connect') as mock_connect:
        mock_websocket = AsyncMock()
        mock_websocket.recv.side_effect = [json.dumps(response) for response in sample_data]
        mock_connect.return_value.__aenter__.return_value = mock_websocket
        yield mock_connect


# Test BinanceWebSocket connection and data handling
@pytest.mark.asyncio
async def test_binance_websocket(mock_db, mock_websockets_connect):
    binance_ws = BinanceWebSocket(db=mock_db)

    with pytest.raises(KeyboardInterrupt):
        await binance_ws.connection()

    assert "BINANCE" in mock_db
    assert "BTCUSDT" in mock_db["BINANCE"]
    assert "ETHUSDT" in mock_db["BINANCE"]
    assert "ask" in mock_db["BINANCE"]["BTCUSDT"]
    assert "bid" in mock_db["BINANCE"]["BTCUSDT"]
    assert "average" in mock_db["BINANCE"]["BTCUSDT"]
