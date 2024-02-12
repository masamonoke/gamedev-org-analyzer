from evaluate import expectation
from flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(expectation, "expectation", 12003, "expectation_service", by_symbol=False)
    app.run()
