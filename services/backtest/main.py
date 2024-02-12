from backtrack import backtrack
from flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(backtrack, "backtest", 12001, "backtest_service")
    app.run()

