import json
import time

import aiohttp
import websockets

from common.views import BaseWebSocketMixin
from src.exceptions import (WebsocketConnectionError,
                            WebsocketMessageSendingError)
from src.settings import MARKETS, logger
from src.utils import calculate_average_value


class KucoinWebSocket(BaseWebSocketMixin):
    '''
    Kukoin include wss channel for retrieving all traging pairs on the exchange
    We need to subscribe to channel and receive the information.
    '''

    def __init__(self, db: dict):
        super().__init__(name=MARKETS["Kucoin"]["name"], db=db, uri=None)

    @staticmethod
    async def get_access_token() -> dict:
        '''
        KuCoin requires an access token from a REST API empty post request for connection to Websocket
        '''
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.kucoin.com/api/v1/bullet-public') as response:
                    response_data = await response.json()
                    ws_token_access = response_data['data']['token']
                    url = f"wss://ws-api-spot.kucoin.com/?token={ws_token_access}"
                    ping_interval = response_data["data"]["instanceServers"][0]["pingInterval"]
                    data = {
                        "url": url,
                        "ping_interval": ping_interval,
                    }
                    return data
        except Exception as e:
            logger.error("Error while fetching assets for Kukoin", str(e))

    async def connection(self) -> None:
        api_data = await self.get_access_token()
        self.uri = api_data["url"]
        ping_interval = api_data["ping_interval"]
        last_ping_time = None

        async def hold_server_connection(
                websocket: websockets.WebSocketClientProtocol,
                ping_interval: int,
        ) -> None:

            # [PING] - Sending message to the websocket for holding connection with the server
            message = {"type": "ping"}
            nonlocal last_ping_time
            try:
                if last_ping_time is None or time.time() - last_ping_time >= ping_interval:
                    last_ping_time = time.time()

                    await websocket.send(json.dumps(message))

                    logger.info("[KukoinAPI Connection] - Sending Ping")
            except Exception as e:
                logger.error(f"Error while sending periodical message: {e}")

        try:
            async with websockets.connect(self.uri) as websocket:
                logger.info("Websocket Connection to KucoinAPI successful")
                try:
                    await self.subscribe_event(websocket)
                except WebsocketMessageSendingError as e:
                    logger.error(str(e))
                    return await self.connection()
                while True:
                    try:
                        await hold_server_connection(websocket, ping_interval)
                    except Exception as e:
                        raise e
                    try:
                        response = await websocket.recv()
                        await self.handler_data(json.loads(response))
                    except Exception as e:
                        logger.error(f"Error while processing WebSocket data: {e}")
                        raise e
        except WebsocketConnectionError as e:
            logger.critical(str(e))
            raise e

    async def subscribe_event(self, websocket: websockets.WebSocketClientProtocol) -> None:
        message = {
            "id": 1545910660739,
            "type": "subscribe",
            "topic": "/market/ticker:all",
            "response": True
        }
        await websocket.send(json.dumps(message))

    async def handler_data(self, data: dict) -> None:
        cache = self.db.setdefault(self.name, {})
        if 'subject' in data:
            for _ in data["data"]:
                try:
                    average_price = calculate_average_value(data["data"]["bestBid"], data["data"]["bestAsk"])
                except (ValueError, TypeError, KeyError) as e:
                    logger.error(f"Error calculating average price for ticker {data['subject']}: {e}  Kucoin")
                    raise e
                cache[data["subject"].replace("-", "")] = {
                    'ask': data["data"]["bestAsk"],
                    'bid': data["data"]["bestBid"],
                    'ask_bid_average': average_price,
                }
