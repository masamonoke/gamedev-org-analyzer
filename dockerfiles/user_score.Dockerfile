FROM python:3.10

ADD services/user_score/user_score.py services/secret.properties .

COPY services/user_score/requirements.txt requirements.txt

ADD services/common common

RUN pip install -r requirements.txt

EXPOSE 12006

ENV DOCKER_CONTAINER 1

CMD ["python", "./user_score.py"]

