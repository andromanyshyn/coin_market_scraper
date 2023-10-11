import logging.config

from loguru import logger

DEBUG = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console"],
            "level": "INFO" if not DEBUG else "DEBUG",
        },
    },
}

logging.config.dictConfig(LOGGING)

logger.level("INFO" if not DEBUG else "DEBUG")

MARKETS = {
    "Kraken": {
        "name": "kraken",
        "endpoint": "wss://ws.kraken.com/",
        "pairs_endpoint": "https://api.kraken.com/0/public/AssetPairs",
    },
    "Binance": {
        "name": "binance",
        "endpoint": "wss://stream.binance.com:9443/ws/!ticker@arr",
    },
    "Huobi": {
        "name": "huobi",
        "endpoint": "wss://api.huobi.pro/ws",
        "pairs_endpoint": "https://api.huobi.pro/v1/common/symbols",
    },
    "Kucoin": {
        "name": "kucoin",
    },
}
