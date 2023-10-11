import re


class CurrencyAggregation:
    def __init__(self, exchange: str, prices: dict, data: dict):
        self.exchange_name = exchange
        self.prices = prices
        self.data = data

    @property
    def aggregation(self) -> None:
        for pair, data in self.prices.items():
            if pair not in self.data:
                self.data[pair] = {}
            self.data[pair][self.exchange_name] = data


def calculate_average_value(buy: str, sell: str) -> float:
    buy_float = float(buy)
    sell_float = float(sell)
    average = (buy_float + sell_float) / 2
    return round(average, 5)


def validate_crypto_pair(pair: str) -> bool:
    pattern = "^[A-Za-z0-9]+$"
    return bool(re.match(pattern, pair))
