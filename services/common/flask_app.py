from flask import Flask, request, Response
import os

from common.evaluator import evaluate
from common.model.company import *
from common.config import config, logging


is_docker = os.environ.get('DOCKER_CONTAINER', False)
if is_docker:
    host = "0.0.0.0"
else:
    host = "localhost"

class FlaskApp:
    def __init__(self, eval_func, route: str, port: int, name: str, host: str = host, by_symbol: bool = True):
        self.eval_func = eval_func
        self.route = route
        self.host = host
        self.port = port
        self.app = Flask(name)

        @self.app.route(f"/{self.route}", methods=["POST"])
        def predict():
            if request.get_data() == b"":
                return Response("Response body is null", status=400, mimetype='application/json')
            companies_scores = company_score_json_to_objects(json.loads(request.get_data()))

            evaluate(companies_scores, self.eval_func, by_symbol=by_symbol)

            response = company_score_objects_to_json(companies_scores)

            logging.info(f"Completed request to {self.route}")

            return response

    def run(self):
        self.app.logger.disabled = True
        is_debug = config["is_debug"]
        if is_debug:
            self.app.run(host=self.host, port=self.port, threaded=True)
        else:
            from waitress import serve
            serve(app=self.app, host=self.host, port=self.port)
