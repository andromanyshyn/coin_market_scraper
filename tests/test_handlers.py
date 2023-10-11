import random
from string import ascii_lowercase

import pytest
import websockets
from httpx import AsyncClient

from markets.binance import BinanceWebSocket
from markets.huobi import HuobiWebSocket
from markets.kraken import KrakenWebSocket
from src.app import DB, app


class TestGeneralAPI:
    @staticmethod
    @pytest.mark.asyncio
    async def test_pair_failed():
        params = {"pair": "BTCUSDT"}

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/currency/", params=params)
            message = response.json()

        assert response.status_code == 400
        assert message == {"detail": "Please specify the exchange"}

    @staticmethod
    @pytest.mark.asyncio
    async def test_pair_wrong_format():
        params = {"pair": "BTC_UDST", "exchange": "binance"}

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/currency/", params=params)
            message = response.json()

        assert response.status_code == 400
        assert message == {"detail": "Please specify the pair in format: a-z; A-Z; or a-z-0-9, example: BTCUSDT"}


class TestWebsocketsHandlers:
    ####################################################################################
    # Binance Handler
    ####################################################################################
    @staticmethod
    @pytest.fixture
    async def generate_valid_data_binance():
        currencies = ["BTCUSDT", "ETHUSD"]
        sample_data = []
        for cur in currencies:
            item = {
                "s": cur,
                "a": round(random.uniform(1995.00, 4995.00), 2),
                "b": round(random.uniform(1995.00, 4995.00), 2),
            }
            sample_data.append(item)
        return sample_data

    @staticmethod
    @pytest.fixture
    def generate_invalid_data_binance():
        currencies = ["BTCUSDT", "ETHUSD"]
        sample_data = []
        for cur in currencies:
            item = {"s": cur, "a": random.choice(ascii_lowercase), "b": round(random.uniform(1995.00, 4995.00), 2)}
            sample_data.append(item)
        return sample_data

    @pytest.mark.asyncio
    async def test_binance_currency_success(self, generate_valid_data_binance: callable):
        binance_ws = BinanceWebSocket(db=DB)
        params = {"exchange": "binance"}

        await binance_ws.handler_data(generate_valid_data_binance)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/currency/", params=params)
            result_data = response.json()

        assert response.status_code == 200
        for element in generate_valid_data_binance:
            ticket = element["s"]
            ask = element["a"]
            bid = element["b"]
            assert ticket in result_data["result"]
            assert ask == result_data["result"][ticket]["ask"]
            assert bid == result_data["result"][ticket]["bid"]

    @pytest.mark.asyncio
    async def test_binance_currency_pair(self, generate_valid_data_binance: callable):
        binance_ws = BinanceWebSocket(db=DB)
        for element in generate_valid_data_binance:
            params = {"pair": element["s"], "exchange": "binance"}

            await binance_ws.handler_data(generate_valid_data_binance)
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/currency/", params=params)
                result_data = response.json()

                ticket = result_data["ticket"]
                ask = result_data["price"]["ask"]
                bid = result_data["price"]["bid"]

                assert response.status_code == 200
                assert ticket == element["s"]
                assert ask == element["a"]
                assert bid == element["b"]

    @pytest.mark.asyncio
    async def test_binance_currency_failed(self, generate_invalid_data_binance: callable):
        binance_ws = BinanceWebSocket(db=DB)

        with pytest.raises(ValueError):
            await binance_ws.handler_data(generate_invalid_data_binance)

    ####################################################################################
    # Kraken Handler
    ####################################################################################
    @staticmethod
    @pytest.fixture
    async def generate_valid_data_kraken():
        currency = "BTCUSDT"
        sample_data = [random.randint(1, 10)]
        item = {"a": [round(random.uniform(1995.00, 4995.00), 2)], "b": [round(random.uniform(1995.00, 4995.00), 2)]}
        sample_data.append(item)
        sample_data.append(currency)
        return sample_data

    @staticmethod
    @pytest.fixture
    def generate_invalid_data_kraken():
        currencies = ["BTCUSDT", "ETHUSD"]
        sample_data = []
        for cur in currencies:
            item = {"s": cur, "a": random.choice(ascii_lowercase), "b": round(random.uniform(1995.00, 4995.00), 2)}
            sample_data.append(item)
        return sample_data

    @pytest.mark.asyncio
    async def test_kraken_currency_success(self, generate_valid_data_kraken: callable):
        kraken_ws = KrakenWebSocket(db=DB)
        params = {"exchange": "kraken"}

        await kraken_ws.handler_data(generate_valid_data_kraken)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/currency/", params=params)
            result_data = response.json()
            print(result_data)

        assert response.status_code == 200
        for _ in generate_valid_data_kraken:
            data = generate_valid_data_kraken[1]
            ticket = generate_valid_data_kraken[-1]
            ask = data["a"][0]
            bid = data["b"][0]
            assert ticket in result_data["result"]
            assert ask == result_data["result"][ticket]["ask"]
            assert bid == result_data["result"][ticket]["bid"]

    @pytest.mark.asyncio
    async def test_kraken_currency_pair(self, generate_valid_data_kraken: callable):
        kraken_ws = KrakenWebSocket(db=DB)
        for _ in generate_valid_data_kraken:
            data = generate_valid_data_kraken[1]
            pair = generate_valid_data_kraken[-1]
            params = {"pair": pair, "exchange": "kraken"}

            await kraken_ws.handler_data(generate_valid_data_kraken)
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/currency/", params=params)
                result_data = response.json()

                ticket = result_data["ticket"]
                ask = result_data["price"]["ask"]
                bid = result_data["price"]["bid"]

                assert response.status_code == 200
                assert ticket == pair
                assert ask == data["a"][0]
                assert bid == data["b"][0]

    @pytest.mark.asyncio
    async def test_kraken_currency_failed(self, generate_invalid_data_kraken):
        kraken_ws = KrakenWebSocket(db=DB)

        with pytest.raises(TypeError):
            await kraken_ws.handler_data(generate_invalid_data_kraken)

    ####################################################################################
    # Huobi Handler
    ####################################################################################
    @staticmethod
    @pytest.fixture
    async def generate_valid_data_huobi():
        currency = "btcusdt"
        item = {
            "ch": f"market.{currency}.ticker",
            "tick": {
                "ask": round(random.uniform(1995.00, 4995.00), 2),
                "bid": round(random.uniform(1995.00, 4995.00), 2),
            },
        }
        return item

    @staticmethod
    @pytest.fixture
    def generate_invalid_data_huobi():
        currency = "btcusdt"
        item = {
            "ch": f"market.{currency}.ticker",
            "tick": {"ask": random.choice(ascii_lowercase), "bid": round(random.uniform(1995.00, 4995.00), 2)},
        }
        return item

    @pytest.mark.asyncio
    async def test_huobi_currency_success(self, generate_valid_data_huobi: callable):
        huobi_ws = HuobiWebSocket(db=DB)
        params = {"exchange": "huobi"}
        websocket = websockets.WebSocketClientProtocol()

        await huobi_ws.handler_data(websocket, generate_valid_data_huobi)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/currency/", params=params)
            result_data = response.json()
        ask = generate_valid_data_huobi["tick"]["ask"]
        bid = generate_valid_data_huobi["tick"]["bid"]
        assert response.status_code == 200
        assert ask == result_data["result"]["BTCUSDT"]["ask"]
        assert bid == result_data["result"]["BTCUSDT"]["bid"]

    @pytest.mark.asyncio
    async def test_huobi_currency_pair(self, generate_valid_data_huobi: callable):
        huobi_ws = HuobiWebSocket(db=DB)
        websocket = websockets.WebSocketClientProtocol()
        pair = generate_valid_data_huobi["ch"].replace("market.", "").replace(".ticker", "").upper()
        params = {"pair": pair, "exchange": "huobi"}

        await huobi_ws.handler_data(websocket, generate_valid_data_huobi)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/currency/", params=params)
            result_data = response.json()

        ticket = result_data["ticket"]
        ask = result_data["price"]["ask"]
        bid = result_data["price"]["bid"]

        assert response.status_code == 200
        assert ticket == pair
        assert ask == generate_valid_data_huobi["tick"]["ask"]
        assert bid == generate_valid_data_huobi["tick"]["bid"]

    @pytest.mark.asyncio
    async def test_huobi_currency_failed(self, generate_invalid_data_huobi: callable):
        huobi_ws = HuobiWebSocket(db=DB)

        with pytest.raises(TypeError):
            await huobi_ws.handler_data(generate_invalid_data_huobi)

    ####################################################################################
    # All Handlers  (case when pair and exchange are not specified)
    ####################################################################################

    @staticmethod
    @pytest.fixture
    async def generate_valid_data():
        currencies = ["BTCUSDT", "ETHUSD"]
        sample_data = []
        for cur in currencies:
            item = {
                "s": cur,
                "a": round(random.uniform(1995.00, 4995.00), 2),
                "b": round(random.uniform(1995.00, 4995.00), 2),
            }
            sample_data.append(item)
        return sample_data

    @staticmethod
    @pytest.fixture
    def generate_invalid_data():
        currencies = ["BTCUSDT", "ETHUSD"]
        sample_data = []
        for cur in currencies:
            item = {"s": cur, "a": random.choice(ascii_lowercase), "b": round(random.uniform(1995.00, 4995.00), 2)}
            sample_data.append(item)
        return sample_data

    @pytest.mark.asyncio
    async def test_handlers_success(
        self,
        generate_valid_data_binance: callable,
        generate_valid_data_kraken: callable,
        generate_valid_data_huobi: callable,
    ):
        binance_ws = BinanceWebSocket(db=DB)
        kraken_ws = KrakenWebSocket(db=DB)
        huobi_ws = HuobiWebSocket(db=DB)

        websocket = websockets.WebSocketClientProtocol()

        await binance_ws.handler_data(generate_valid_data_binance)
        await kraken_ws.handler_data(generate_valid_data_kraken)
        await huobi_ws.handler_data(websocket, generate_valid_data_huobi)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/currency/")
            result_data = response.json()
        assert response.status_code == 200
        assert "binance" in result_data["result"]["BTCUSDT"]
        assert "kraken" in result_data["result"]["BTCUSDT"]
        assert "huobi" in result_data["result"]["BTCUSDT"]
