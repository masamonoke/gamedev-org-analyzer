from backtrack import backtrack

import sys
sys.path.append("../")
from flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(backtrack, "backtest", 12001, "backtest_service")
    app.run()

