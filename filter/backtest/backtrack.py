import backtrader as bt
import yfinance as yf

import datetime as dt
from dateutil.relativedelta import relativedelta
import sys
import logging
sys.path.append("../")
from loader.loader import get_ticker_data
from threading import Lock

logging.basicConfig(level=logging.INFO)

def backtrack(ticker: str, lock: Lock) -> float:
    logging.info(f"Started backtrack {ticker}")
    cerebro = bt.Cerebro()
    start = dt.datetime.now() - relativedelta(months=5)
    # df = yf.download(ticket, start=start)
    df = get_ticker_data(ticker, start, lock)
    feed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(feed)
    cerebro.addstrategy(SmaCross)
    cerebro.broker.setcommission(commission=0.005)
    before_test_funds = cerebro.broker.getvalue()
    cerebro.run()
    after_test_funds = cerebro.broker.get_value()
    diff = after_test_funds - before_test_funds
    return diff

class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30   # period for the slow moving average
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

def main():
    if len(sys.argv) < 2:
        print("usage: python backtrack.py <stock symbol>")
        return
    symbol = sys.argv[1]
    diff = backtrack(symbol)
    print(f"The difference is {diff}")


if __name__ == "__main__":
    main()
