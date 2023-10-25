import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
import datetime as dt
from sklearn.preprocessing import MinMaxScaler
from dateutil.relativedelta import relativedelta
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.models import Sequential
import time
import sys
import logging

logging.basicConfig(level=logging.INFO)

# the more years the more accurate prediction but training is too long. One year is too short
def _load_data(symbol: str, years: int = 1) -> pd.DataFrame:
    start = dt.datetime.now() - relativedelta(years=years)
    data = yf.download(symbol, start=start)
    return data

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

def _predict(y:  np.ndarray) -> np.ndarray:
    n_lookback = 60  # length of input sequences (lookback period)
    n_forecast = 7  # length of output sequences (forecast period)
    X = []
    Y = []
    for i in range(n_lookback, len(y) - n_forecast + 1):
        X.append(y[i - n_lookback: i])
        Y.append(y[i: i + n_forecast])

    start = time.time()
    X = np.array(X)
    Y = np.array(Y)
    logging.info("Building model...")
    model = __build_model(n_lookback, n_forecast)
    model.fit(X, Y, epochs=100, batch_size=32, verbose=0)
    # generate the forecasts
    X_ = y[- n_lookback:]  # last available input sequence
    X_ = X_.reshape(1, n_lookback, 1)
    Y_ = model.predict(X_).reshape(-1, 1)
    return Y_

def evaluate_stocks(symbol: str) -> float:
    data = _load_data(symbol)
    y = _y(data)
    last_actual = y[-1]
    forecast = _predict(y)
    last_predicted = forecast[-1]
    score = last_predicted - last_actual
    score = float(score)
    return score

def main():
    if len(sys.argv) < 2:
        logging.error("usage: lstm_predict <stock symbol>")
        return
    symbol = sys.argv[1]
    score = evaluate_stocks(symbol)
    print(f"{symbol} stock score is {score}")

if __name__ == "__main__":
    main()
