FROM python:3.10

ADD services/stock_predict/stock_predict.py services/secret.properties .

COPY services/stock_predict/requirements.txt requirements.txt

ADD services/common common

RUN pip install -r requirements.txt

EXPOSE 12000

ENV DOCKER_CONTAINER 1

CMD ["python", "./stock_predict.py"]

