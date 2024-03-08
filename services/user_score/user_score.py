from common.user_score import user_score
from common.flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(eval_func=user_score, route="user_score", port=12006, name="user_score_service", by_symbol=False)
    app.run()
