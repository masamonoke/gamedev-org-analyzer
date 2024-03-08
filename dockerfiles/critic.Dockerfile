FROM python:3.10

ADD services/critic/critic.py services/secret.properties .

COPY services/critic/requirements.txt requirements.txt

ADD services/common common

RUN pip install -r requirements.txt

EXPOSE 12005

ENV DOCKER_CONTAINER 1

CMD ["python", "./critic.py"]

