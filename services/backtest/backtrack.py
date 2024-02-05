import datetime as dt
import sys
from threading import Lock

import backtrader as bt
from dateutil.relativedelta import relativedelta

sys.path.append("../")
from config import logging
from loader.loader import get_ticker_data
from cache import TimedCache

backtest_cache = TimedCache()


# TODO: cache for symbol with day timeout and synchronize getting and setting
def backtrack(ticker: str, lock: Lock) -> float:
    logging.info(f"Backtracking {ticker}")

    if backtest_cache.exists(ticker):
        return backtest_cache.get(ticker)

    cerebro = bt.Cerebro()
    start = dt.datetime.now() - relativedelta(years=1)
    df = get_ticker_data(ticker, start, lock)
    feed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(feed)
    cerebro.addstrategy(SmaCross)
    cerebro.broker.setcommission(commission=0.005)
    before_test_funds = cerebro.broker.getvalue()
    cerebro.run()
    after_test_funds = cerebro.broker.get_value()
    diff = after_test_funds - before_test_funds

    logging.info(f"Backtracking score for company {ticker} is {diff}")

    backtest_cache.add(ticker, diff)

    return diff


class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30  # period for the slow moving average
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

    def next(self):
        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.buy()  # enter long

        elif self.crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position
