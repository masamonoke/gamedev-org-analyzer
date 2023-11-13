from flask import Flask, request, Response
from types import SimpleNamespace
from dataclasses import dataclass
import sys
from backtrack import backtrack
sys.path.append("../")
from model.company import *
from filter import evaluate

app = Flask(__name__)

@app.route("/backtest", methods=["POST"])
def backtrack_report():
    if request.get_data() == b"":
        return Response("Response body is null", status=400, mimetype='application/json')
    companies_scores = company_score_json_to_objects(json.loads(request.get_data()))

    evaluate(companies_scores, backtrack)

    response = company_score_objects_to_json(companies_scores)
    return response

if __name__ == "__main__":
    app.run(host="localhost", port="12001", threaded=True)
