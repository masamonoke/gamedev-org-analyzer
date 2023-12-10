from comments import evaluate_comments

import sys
sys.path.append("../")
from flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(evaluate_comments, "predict", "12002", by_symbol=False)
    app.run()

