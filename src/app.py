import asyncio

from fastapi import FastAPI, HTTPException, Query

from markets.binance import BinanceWebSocket
from markets.kraken import KrakenWebSocket
from markets.bitfinex import BitfinexWebSocket
from .settings import logger
from .utils import CurrencyAggregation

DB = {}

app = FastAPI()


@app.on_event('startup')
async def run_ws():
    binance = BinanceWebSocket(DB)
    kraken = KrakenWebSocket(DB)
    bitfinex = BitfinexWebSocket(DB)
    try:
        # asyncio.create_task(binance.connection())
        asyncio.create_task(bitfinex.connection())
        # asyncio.create_task(kraken.connection())
    except asyncio.exceptions.TimeoutError as e:
        logger.critical(f'Connection failed: {e}')
        await run_ws()


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
