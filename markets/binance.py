import json
import websockets
from common.views import BaseWebSocketMixin
from src.exceptions import WebsocketConnectionError
from src.settings import MARKETS, logger
from src.utils import calculate_average_value


class BinanceWebSocket(BaseWebSocketMixin):
    def __init__(self, db: dict):
        super().__init__(name=MARKETS["Binance"]["name"], uri=MARKETS["Binance"]["endpoint"], db=db)

    '''
    Binance has !ticker@arr endpoint which response for all current pairs with have updates. 
    No need request any pairs before or subscribe for all pairs one by one.
    '''

    # method for establishing the WebSocket connection.
    async def connection(self) -> None:
        try:
            async with websockets.connect(self.uri) as websocket:
                logger.info("Websocket Connection to BinanceAPI successful")
                while True:
                    try:
                        # Receive WebSocket data from the connection.
                        response = await websocket.recv()
                        await self.handler_data(json.loads(response))
                    except Exception as error:
                        logger.error(f"Error while processing WebSocket data: {error}")
                        raise error
        except WebsocketConnectionError as e:
            logger.critical(str(e))
            raise e

    # handling WebSocket data
    async def handler_data(self, data: list[dict]) -> None:
        cache = self.db.setdefault(self.name, {})
        for ticker in data:
            try:
                # Calculate the average price from the 'ask' and 'bid' values in the ticker data.
                average_price = calculate_average_value(ticker["b"], ticker["a"])
            except (ValueError, TypeError) as e:
                logger.error(f"Error calculating average price for ticker {ticker['s']}: {e}")
                raise e
            cache[ticker['s']] = {
                'ask': ticker['a'],
                'bid': ticker['b'],
                'ask_bid_average': average_price,
            }
