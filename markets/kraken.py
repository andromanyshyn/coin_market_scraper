import asyncio
import json

import aiohttp
import websockets

from common.views import BaseWebSocket
from src.exceptions import (WebsocketConnectionError,
                            WebsocketMessageSendingError)
from src.settings import MARKETS, logger
from src.utils import calculate_average_value


class KrakenWebSocket(BaseWebSocket):
    def __init__(self, db):
        super().__init__(name=MARKETS["KRAKEN"]["name"], uri=MARKETS["KRAKEN"]["endpoint"], db=db)

    @staticmethod
    async def fetch(session: aiohttp.ClientSession, url: str) -> dict:
        async with session.get(url) as response:
            return await response.json()

    async def fetch_kraken_pairs(self):
        url = MARKETS["KRAKEN"]["pairs_endpoint"]
        tasks = []
        async with aiohttp.ClientSession() as session:
            tasks.append(self.fetch(session, url))
            data = await asyncio.gather(*tasks)
            pairs = data[0]["result"]
            all_pairs = [pairs[pair]["wsname"] for pair in pairs]
            return all_pairs

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
        await websocket.send(json.dumps(message))

    async def handler_data(self, data) -> None:
        cache = self.db.setdefault(self.name, {})
        if isinstance(data, list):
            currency_data = data[1]
            for _ in currency_data:
                average_price = await calculate_average_value(currency_data["b"][0], currency_data["a"][0])
                cache[data[-1].replace("/", "")] = {
                    "buy": currency_data["b"][0],
                    "sell": currency_data["a"][0],
                    "average": average_price,
                }
