import sys

sys.path.append("../")
from common.open_critic import critic_score
from common.flask_app import FlaskApp

if __name__ == "__main__":
    app = FlaskApp(eval_func=critic_score, route="critic", port=12005, name="critic_score__service", by_symbol=False)
    app.run()

