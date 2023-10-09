import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Query

from markets.binance import BinanceWebSocket
from markets.kraken import KrakenWebSocket
from settings import logger
from utils import CurrencyAggregation


def main():
    DB = {}

    @asynccontextmanager
    async def run_ws(app: FastAPI):
        binance = BinanceWebSocket(DB)
        kraken = KrakenWebSocket(DB)
        try:
            binance_event = asyncio.create_task(binance.connection())
            kraken_event = asyncio.create_task(kraken.connection())
        except Exception as e:
            logger.critical(f'Connection failed: {e}')
            raise e
        yield
        binance_event.cancel()
        kraken_event.cancel()

    app = FastAPI(lifespan=run_ws)

    @app.get("/")
    async def main(pair: str = Query(None), exchange: str = Query(None)) -> dict:
        aggregated_prices = {}
        if pair and exchange:
            pair = pair.upper()
            exchange = exchange.lower()
            if exchange in DB.keys() and pair in DB[exchange]:
                return {"result": {
                    "ticket": pair,
                    "buy": DB[exchange][pair]["buy"],
                    "sell": DB[exchange][pair]["sell"],
                    "average": DB[exchange][pair]["average"]}
                }
            else:
                raise HTTPException(status_code=404, detail="Pair not found")
        if not pair and exchange:
            exchange = exchange.lower()
            if exchange in DB.keys():
                return {"result": DB[exchange]}
            else:
                raise HTTPException(status_code=404, detail="Exchange not found")

        if pair and not exchange:
            raise HTTPException(status_code=400, detail="Please specify the exchange")
        for exchange in DB:
            for currency in DB[exchange]:
                cur_dict = {currency: DB[exchange][currency]}
                aggregate = CurrencyAggregation(exchange, cur_dict, aggregated_prices)
                await aggregate.aggregation

        return {"result": aggregated_prices}

    try:
        uvicorn.run(app, host="localhost", port=5555)
    except Exception as error:
        logger.critical(f"uvicorn.error: {error}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f'An error occurred while starting the application: {str(e)}')
        raise e
