import asyncio
import json

import aiohttp
import websockets

from common.views import BaseWebSocketMixin
from src.exceptions import (WebsocketConnectionError,
                            WebsocketMessageSendingError)
from src.settings import MARKETS, logger
from src.utils import calculate_average_value


class KrakenWebSocket(BaseWebSocketMixin):
    '''
    Kraken include API endpoint for retrieving all traging pairs on the exchange
    Before starting connection with main Kraken websocket for loading market data with price for all trading pairs,
    we collect primary information about all assets
    '''

    def __init__(self, db):
        super().__init__(name=MARKETS["Kraken"]["name"], uri=MARKETS["Kraken"]["endpoint"], db=db)

    @staticmethod
    async def fetch(session: aiohttp.ClientSession, url: str) -> dict:
        async with session.get(url) as response:
            return await response.json()

    async def fetch_kraken_pairs(self) -> list:
        url = MARKETS["Kraken"]["pairs_endpoint"]
        tasks = []
        try:
            async with aiohttp.ClientSession() as session:
                tasks.append(self.fetch(session, url))
                data = await asyncio.gather(*tasks)
                pairs = data[0]["result"]
                assets = [pairs[pair]["wsname"] for pair in pairs]
                return assets
        except Exception as e:
            logger.error("Error while fetching assets for Kraken", str(e))

    async def connection(self) -> None:
        try:
            async with websockets.connect(self.uri) as websocket:
                logger.info("Websocket Connection to KrakenAPI successful")
                try:
                    await self.send_websocket_message(websocket)
                except WebsocketMessageSendingError as e:
                    logger.error(str(e))
                    return await self.connection()
                while True:
                    try:
                        response = await websocket.recv()
                        await self.handler_data(json.loads(response))
                    except Exception as e:
                        logger.error(f"Error while processing WebSocket data: {e}")
                        raise e
        except WebsocketConnectionError as e:
            logger.critical(str(e))
            raise e

    async def send_websocket_message(self, websocket: websockets.WebSocketClientProtocol) -> None:
        pairs = await self.fetch_kraken_pairs()
        message = {"event": "subscribe", "pair": pairs, "subscription": {"name": "ticker"}}
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error("Error while sending message to Kraken websocket", str(e))

    async def handler_data(self, data: list) -> None:
        cache = self.db.setdefault(self.name, {})
        if isinstance(data, list):
            currency_data = data[1]
            for _ in currency_data:
                try:
                    average_price = calculate_average_value(currency_data["b"][0], currency_data["a"][0])
                except (ValueError, TypeError, KeyError) as e:
                    logger.error(f"Error calculating average price for ticker {data[-1]}: {e}  Kraken")
                    raise e
                cache[data[-1].replace("/", "")] = {
                    "ask": currency_data["a"][0],
                    "bid": currency_data["b"][0],
                    "ask_bid_average": average_price,
                }
