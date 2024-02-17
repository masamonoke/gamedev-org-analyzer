import numpy as np
import pandas as pd
import datetime as dt
from sklearn.preprocessing import MinMaxScaler
from dateutil.relativedelta import relativedelta
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.models import Sequential
from threading import Lock

from common.config import logging
from common.loader.loader import get_ticker_data
from common.cache import TimedCache

lstm_cache = TimedCache()


def _y(data: pd.DataFrame) -> np.ndarray:
    y = data["Close"]
    y = y.values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler = scaler.fit(y, scaler)
    y = scaler.transform(y)
    return y


def __build_model(lookback_days: int, predict_days: int) -> Sequential:
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(lookback_days, 1)))
    model.add(LSTM(units=50))
    model.add(Dense(predict_days))
    model.compile(loss='mean_squared_error', optimizer='adam')
    return model


def _predict(y: np.ndarray) -> np.ndarray:
    n_lookback = 60  # length of input sequences (lookback period)
    n_forecast = 7  # length of output sequences (forecast period)
    X = []
    Y = []
    for i in range(n_lookback, len(y) - n_forecast + 1):
        X.append(y[i - n_lookback: i])
        Y.append(y[i: i + n_forecast])

    X = np.array(X)
    Y = np.array(Y)
    logging.debug("Building model...")
    model = __build_model(n_lookback, n_forecast)
    model.fit(X, Y, epochs=100, batch_size=32, verbose=0)
    # generate the forecasts
    X_ = y[- n_lookback:]  # last available input sequence
    X_ = X_.reshape(1, n_lookback, 1)
    Y_ = model.predict(X_).reshape(-1, 1)
    return Y_


YEARS = 2


def stocks(symbol: str, lock: Lock) -> float:
    logging.info(f"Predicting stock price for {symbol}")

    if lstm_cache.exists(symbol):
        return lstm_cache.get(symbol)

    start = dt.datetime.now() - relativedelta(years=YEARS)
    data = get_ticker_data(symbol, start, lock)
    y = _y(data)
    last_actual = y[-1]
    forecast = _predict(y)
    last_predicted = forecast[-1]
    score = last_predicted - last_actual
    score = float(score)
    logging.info(f"Predicted stocks price score for company {symbol} is {score}")

    lstm_cache.add(symbol, score)

    return score
