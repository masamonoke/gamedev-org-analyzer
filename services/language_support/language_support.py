from common.language import language_support
from common.flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(eval_func=language_support, route="language_support", port=12003, name="language_support_service", by_symbol=False)
    app.run()

