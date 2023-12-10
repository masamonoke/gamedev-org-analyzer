from lstm_predict import evaluate_stocks

import sys
sys.path.append("../")
from flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(evaluate_stocks, "predict", "12000")
    app.run()
