from common.games_released import games_released_count
from common.flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(eval_func=games_released_count, route="games_release", port=12007, name="games_release_service", by_symbol=False)
    app.run()
