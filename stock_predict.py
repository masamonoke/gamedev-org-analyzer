from common.lstm_predict import stocks
from common.flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(stocks, "stock_predict", 12000, "stocks_predict_service")
    app.run()
