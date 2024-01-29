import logging

from flask import Flask, request, Response

from filter import evaluate
from model.company import *

logging.basicConfig(level=logging.INFO)


class FlaskApp:
    def __init__(self, eval_func, route: str, port: str, host: str = "localhost", by_symbol: bool = True):
        self.eval_func = eval_func
        self.route = route
        self.host = host
        self.port = port
        self.app = Flask(__name__)

        @self.app.route(f"/{self.route}", methods=["POST"])
        def predict():
            if request.get_data() == b"":
                return Response("Response body is null", status=400, mimetype='application/json')
            companies_scores = company_score_json_to_objects(json.loads(request.get_data()))

            evaluate(companies_scores, self.eval_func, by_symbol=by_symbol)

            response = company_score_objects_to_json(companies_scores)
            return response

    def run(self):
        self.app.run(host=self.host, port=self.port, threaded=True)
