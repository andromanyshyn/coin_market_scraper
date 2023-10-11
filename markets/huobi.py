import asyncio
import json
import gzip

import aiohttp
import websockets

from common.views import BaseWebSocketMixin
from src.exceptions import WebsocketConnectionError, WebsocketMessageSendingError
from src.settings import MARKETS, logger
from src.utils import calculate_average_value


class HuobiWebSocket(BaseWebSocketMixin):
    '''
    Huobi WebSocket requires REST API request for symbols.
    Huobi haven't connection to all trading pairs or ticker, which response with trading symbols for
    Websocket Market Data subscribe.
    We Need to create a subscription request for each trading pair
    '''

    def __init__(self, db: dict):
        super().__init__(name=MARKETS["Huobi"]["name"], uri=MARKETS["Huobi"]["endpoint"], db=db)

    @staticmethod
    async def fetch(session: aiohttp.ClientSession, url: str) -> dict:
        async with session.get(url) as response:
            return await response.json()

    async def fetch_huobi_assets(self) -> tuple:
        url = MARKETS["Huobi"]["pairs_endpoint"]
        tasks = []
        try:
            async with aiohttp.ClientSession() as session:
                tasks.append(self.fetch(session, url))
                data = await asyncio.gather(*tasks)
                return data
        except Exception as e:
            logger.error("Error while fetching assets for Huobi", str(e))

    async def connection(self) -> None:
        try:
            async with websockets.connect(self.uri) as websocket:
                logger.info("Websocket Connection to HuobiAPI successful")
                try:
                    await self.send_websocket_message(websocket)
                except WebsocketMessageSendingError as e:
                    logger.error(str(e))
                    return await self.connection()
                while True:
                    try:
                        response = await websocket.recv()
                        decoded_response = gzip.decompress(response).decode('utf-8')
                    except Exception as e:
                        logger.error("Error while decoding response from HuobiAPI", str(e))
                        raise e
                    try:
                        await self.handler_data(websocket, json.loads(decoded_response))
                    except Exception as e:
                        logger.error(f"Error while processing WebSocket data: {e}")
                        raise e
        except WebsocketConnectionError as e:
            logger.critical(str(e))
            raise e

    async def send_websocket_message(self, websocket: websockets.WebSocketClientProtocol) -> None:
        assets_list = await self.fetch_huobi_assets()
        for element in assets_list:
            for asset in element["data"]:
                if asset['state'] == 'online':
                    try:
                        subscribe = {
                            "sub": f"market.{asset['symbol']}.ticker"
                        }
                        await websocket.send(json.dumps(subscribe))
                    except Exception as e:
                        raise e

    async def handler_data(self, websocket: websockets.WebSocketClientProtocol, data: dict) -> None:
        cache = self.db.setdefault(self.name, {})
        if 'ping' in data:
            try:
                await websocket.send(json.dumps({'pong': data['ping']}))
            except Exception as e:
                logger.error(str(e))
                raise e

        elif 'ch' in data:
            name = data['ch'].replace('market.', '').replace('.ticker', '').upper()
            try:
                average = calculate_average_value(data["tick"]["ask"], data["tick"]["bid"])
            except (ValueError, TypeError, KeyError) as e:
                logger.error(f"Error calculating average price for ticker {name}: {e}  Huobi")
                raise e
            cache[name] = {
                "ask": data["tick"]["ask"],
                "bid": data["tick"]["bid"],
                "ask_bid_average": average,
            }
