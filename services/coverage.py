import sys

sys.path.append("../")
from common.coverage import coverage
from common.flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(eval_func=coverage, route="coverage", port=12003, name="coverage_service", by_symbol=False)
    app.run()
