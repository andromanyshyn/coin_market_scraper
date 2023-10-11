import asyncio

from fastapi import FastAPI, HTTPException, Query

from markets.binance import BinanceWebSocket
from markets.kraken import KrakenWebSocket
from markets.huobi import HuobiWebSocket
from markets.kucoin import KucoinWebSocket
from .settings import logger
from .utils import CurrencyAggregation, validate_crypto_pair

DB = {}

app = FastAPI()


@app.on_event('startup')
async def run_ws():
    binance = BinanceWebSocket(DB)
    kraken = KrakenWebSocket(DB)
    huobi = HuobiWebSocket(DB)
    kucoin = KucoinWebSocket(DB)
    try:
        asyncio.create_task(binance.connection())
        asyncio.create_task(huobi.connection())
        asyncio.create_task(kraken.connection())
        asyncio.create_task(kucoin.connection())
    except asyncio.exceptions.TimeoutError as e:
        logger.critical(f'Connection failed: {e}')
        return run_ws()


@app.get("/")
async def main(pair: str = Query(None), exchange: str = Query(None)) -> dict:
    aggregated_prices = {}
    if pair and exchange:
        if not validate_crypto_pair(pair):
            raise HTTPException(
                status_code=400, detail="Please specify the pair in format: a-z; A-Z; or a-z-0-9, example: BTCUSDT"
            )
        pair = pair.upper()
        exchange = exchange.lower()
        if exchange not in DB.keys():
            raise HTTPException(status_code=404, detail=f"Pleasy specify one of available exchanges {list(DB.keys())}")
        if pair not in DB[exchange]:
            raise HTTPException(status_code=404, detail="Pair not found")
        return {"ticket": pair,
                "price": {"ask": DB[exchange][pair]["ask"], "bid": DB[exchange][pair]["bid"],
                          "ask_bid_average": DB[exchange][pair]["ask_bid_average"]}
                }
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
            try:
                aggregate.aggregation
            except Exception as e:
                raise e

    return {"result": aggregated_prices}
