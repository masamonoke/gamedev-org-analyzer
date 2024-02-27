import sys

sys.path.append("../")
from common.fundamental_analysis import f_score
from common.flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(eval_func=f_score, route="fundamental", port=12004, name="fundamental_analysis_service", by_symbol=True)
    app.run()

