FROM python:3.10

ADD services/games_released/games_released.py services/secret.properties .

COPY services/games_released/requirements.txt requirements.txt

ADD services/common common

RUN pip install -r requirements.txt

EXPOSE 12007

ENV DOCKER_CONTAINER 1

CMD ["python", "./games_released.py"]

