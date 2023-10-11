# CryptoFastAPI
Binance, Huobi, KuCoin, Kraken FastAPI application with websockets real time market price for all available trading pairs


# Crypto Price Aggregator

This is a comprehensive API service developed to retrieve real-time price data from multiple crypto exchanges, including Binance and Kraken. The service is built using Python 3.x and the FastAPI framework, with a WebSocket connection to fetch price data. The application allows users to fetch data for any currency pair from the specified exchanges.

## Requirements

- Python 3.x
- FastAPI
- websockets
- json
- requests
- gzip
- Docker



## Usage

### Fetching Crypto Price Data

You can fetch real-time crypto price data using the API endpoints.

#### Fetch all prices from both exchanges (aggregated)

```http
GET /currency/
```

#### Fetch all prices from a specific exchange

```http
GET /currency/?exchange=binance
```

#### Fetch prices for a specific currency pair from a specific exchange

```http
GET /currency/?exchange=kraken&pair=btcusdt
```


## Logging

I use loguru library for logging.


## Code Guidelines

- Code is written in Python 3.x following PEP 8 style guidelines.
- WebSocket connections are established for real-time data retrieval.
- The application utilizes asynchronous programming for efficient handling of multiple connections.
- The application does not rely on real-time REST API requests during API service calls.
- Data normalization is performed for currency pair names to ensure consistency.
- The application does not require a database and does not save any data.

Note: Some exchanges required a `REST API` request before starting web sockets to get an access token or a list of assets due to the inability to get a list of assets using websockets and the need to `subscribe` to all trading pairs in turn.
