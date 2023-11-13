from flask import Flask, request, Response
import json
from types import SimpleNamespace
from dataclasses import dataclass
import sys
from threading import Thread, Lock
import logging
from lstm_predict import *

sys.path.append("../")
from model.company import *
from filter import evaluate

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    if request.get_data() == b"":
        return Response("Response body is null", status=400, mimetype='application/json')
    companies_scores = company_score_json_to_objects(json.loads(request.get_data()))

    evaluate(companies_scores, evaluate_stocks)
    # tasks = []
    # lock = Lock()
    # for score in companies_scores:
    #     tasks.append(Thread(target=_evaluate, args=(score, lock,)))
    # for t in tasks:
    #     t.start()
    # for t in tasks:
    #     t.join()

    response = company_score_objects_to_json(companies_scores)
    return response

# def _evaluate(score, lock: Lock):
#     s = evaluate_stocks(score.company.symbol, lock)
#     lock.acquire()
#     score.total_score += s
#     lock.release()

if __name__ == "__main__":
    app.run(host="localhost", port="12000", threaded=True)
