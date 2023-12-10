from pandas import DataFrame
import yfinance as yf
import datetime as dt
import logging
from threading import Lock

logging.basicConfig(format='%(asctime)s, %(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO)

ticker_data = {}

def get_ticker_data(ticker: str, start, lock: Lock, end=dt.datetime.now()) -> DataFrame:
    logging.info(f"Getting ticker data {ticker} from {start} to nowadays")
    if ticker in ticker_data:
        logging.info(f"{ticker} data is present in cache")
        df = ticker_data[ticker]
        format = "%Y-%m-%d"
        start_time_present = df.index[0]
        if type(start) == str:
            start_time = dt.datetime.strptime(start, format)
        else:
            start_time = start
        if start_time < start_time_present:
            lock.acquire()
            logging.info(f"{ticker} data is not enough old. Redownload")
            ticker_data[ticker] = yf.download(ticker, start=start, end=end)
            lock.release()
    else:
        lock.acquire()
        if ticker not in ticker_data:
            logging.info(f"New ticker data: {ticker}. Download")
            ticker_data[ticker] = yf.download(ticker, start=start, end=end)
        lock.release()

    df = ticker_data[ticker]
    return df.loc[:end]
