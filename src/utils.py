class CurrencyAggregation:
    def __init__(self, exchange: str, prices: dict, data: dict):
        self.exchange_name = exchange
        self.prices = prices
        self.data = data

    @property
    async def aggregation(self):
        for pair, data in self.prices.items():
            if pair not in self.data:
                self.data[pair] = {}
            self.data[pair][self.exchange_name] = data


async def calculate_average_value(buy: str, sell: str) -> float:
    buy_float = float(buy)
    sell_float = float(sell)
    return (buy_float + sell_float) / 2
