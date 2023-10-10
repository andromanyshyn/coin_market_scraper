import json

import websockets

from common.views import BaseWebSocket
from src.exceptions import WebsocketConnectionError
from src.settings import MARKETS, logger
from src.utils import calculate_average_value


class BinanceWebSocket(BaseWebSocket):
    def __init__(self, db):
        super().__init__(name=MARKETS["Binance"]["name"], uri=MARKETS["Binance"]["endpoint"], db=db)

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

    async def handler_data(self, data) -> None:
        cache = self.db.setdefault(self.name, {})
        print(["DATA"], data)
        if isinstance(data, dict):
            lst = []
            lst.append(data)
            data = lst
        for ticker in data:
            try:
                average_price = await calculate_average_value(ticker["b"], ticker["a"])
            except TypeError as e:
                raise e
            cache[ticker['s']] = {
                'ask': ticker['a'],
                'bid': ticker['b'],
                'average': average_price,
            }
