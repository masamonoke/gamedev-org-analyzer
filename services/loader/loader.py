from pandas import DataFrame
import yfinance as yf
import datetime as dt
from threading import Lock
import sys

sys.path.append("../")
from config import logging

ticker_data = {}


def get_ticker_data(ticker: str, start, lock: Lock, end: dt.datetime = dt.datetime.now()) -> DataFrame:
    logging.debug(f"Getting ticker data {ticker} from {start} to nowadays")
    if ticker in ticker_data:
        logging.debug(f"{ticker} data is present in cache")
        df = ticker_data[ticker]
        format = "%Y-%m-%d"
        start_time_present = df.index[0]
        if type(start) == str:
            start_time = dt.datetime.strptime(start, format)
        else:
            start_time = start
        if start_time < start_time_present:
            lock.acquire()
            logging.debug(f"{ticker} data is not enough old. Redownload")
            ticker_data[ticker] = yf.download(ticker, start=start, end=end)
            lock.release()
    else:
        lock.acquire()
        if ticker not in ticker_data:
            logging.debug(f"New ticker data: {ticker}. Download")
            ticker_data[ticker] = yf.download(ticker, start=start, end=end)
        lock.release()

    df = ticker_data[ticker]
    return df.loc[:end]
