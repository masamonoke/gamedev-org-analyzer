import datetime as dt
from threading import Lock

import backtrader as bt
from dateutil.relativedelta import relativedelta

from common.config import logging
from common.loader.loader import get_ticker_data
from common.cache import TimedCache

backtest_cache = TimedCache()

#for reference https://www.backtrader.com/docu/quickstart/quickstart/

# TODO: redo
# TODO: cache for symbol with day timeout and synchronize getting and setting
def backtrack(ticker: str, lock: Lock) -> float:
    logging.info(f"Backtracking {ticker}")

    if backtest_cache.exists(ticker):
        return backtest_cache.get(ticker)

    cerebro = bt.Cerebro()
    start = dt.datetime.now() - relativedelta(months=5)
    df = get_ticker_data(ticker, start, lock)
    feed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(feed)
    cerebro.addstrategy(SmaCross)
    cerebro.broker.setcommission(commission=0.005)
    before_test_funds = cerebro.broker.getvalue()
    cerebro.run()
    after_test_funds = cerebro.broker.get_value()
    diff = 100 * (after_test_funds - before_test_funds) / ((after_test_funds + before_test_funds) / 2)

    logging.info(f"Backtracking score for company {ticker} is {diff}")

    backtest_cache.add(ticker, diff)

    return diff


class SmaCross(bt.Strategy):
    params = dict(
        pfast=10,
        pslow=30
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)
        sma2 = bt.ind.SMA(period=self.p.pslow)
        self.crossover = bt.ind.CrossOver(sma1, sma2)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()

        elif self.crossover < 0:
            self.close()
