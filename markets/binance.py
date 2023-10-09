import json

import websockets

from common.views import BaseWebSocket
from src.exceptions import WebsocketConnectionError
from src.settings import MARKETS, logger
from src.utils import calculate_average_value


class BinanceWebSocket(BaseWebSocket):
    def __init__(self, db):
        super().__init__(name=MARKETS["BINANCE"]["name"], uri=MARKETS["BINANCE"]["endpoint"], db=db)

    async def connection(self) -> None:
        try:
            async with websockets.connect(self.uri) as websocket:
                logger.info("Websocket Connection to BinanceAPI successful")
                while True:
                    try:
                        response = await websocket.recv()
                        await self.handler_data(json.loads(response))
                    except Exception as error:
                        logger.error(f"Error while processing WebSocket data: {error}")
                        raise error
        except WebsocketConnectionError as e:
            logger.critical(str(e))
            raise e

    async def handler_data(self, data: list[dict]) -> None:
        cache = self.db.setdefault(self.name, {})
        for ticker in data:
            average_price = await calculate_average_value(ticker["b"], ticker["a"])
            cache[ticker['s']] = {
                'ask': ticker['a'],
                'bid': ticker['b'],
                'average': average_price,
            }
