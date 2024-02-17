from common.coverage import coverage
from common.flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(coverage, "coverage", 12003, "coverage_service", by_symbol=False)
    app.run()
