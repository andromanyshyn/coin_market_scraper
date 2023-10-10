import json

import websockets

from common.views import BaseWebSocket
from src.exceptions import WebsocketConnectionError, WebsocketMessageSendingError
from src.settings import MARKETS, logger
from src.utils import calculate_average_value


class BitfinexWebSocket(BaseWebSocket):
    def __init__(self, db):
        super().__init__(name=MARKETS["Bitfinex"]["name"], uri=MARKETS["Bitfinex"]["endpoint"], db=db)

    async def connection(self) -> None:
        try:
            async with websockets.connect(self.uri) as websocket:
                logger.info("Websocket Connection to Bitfinex successful")
                while True:
                    try:
                        await self.send_websocket_message(websocket)
                    except WebsocketMessageSendingError as e:
                        logger.error(str(e))
                    try:
                        response = await websocket.recv()
                        print(response)
                        await self.handler_data(json.loads(response))
                    except Exception as error:
                        logger.error(f"Error while processing WebSocket data: {error}")
                        raise error
        except WebsocketConnectionError as e:
            logger.critical(str(e))
            raise e

    async def send_websocket_message(self, websocket: websockets.WebSocketClientProtocol) -> None:
        # pairs = await self.fetch_kraken_pairs()
        message = {"event": "subscribe", "channel": "ticker", "symbol": "tBTCUSD"}
        await websocket.send(json.dumps(message))

    async def handler_data(self, data) -> None:
        print(data)
        # cache = self.db.setdefault(self.name, {})
        # for ticker in data:
        #     try:
        #         average_price = await calculate_average_value(ticker["b"], ticker["a"])
        #     except TypeError as e:
        #         raise e
        #     cache[ticker['s']] = {
        #         'ask': ticker['a'],
        #         'bid': ticker['b'],
        #         'average': average_price,
        #     }
