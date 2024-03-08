FROM python:3.10

ADD services/igdb_cache/igdb_cache.py services/secret.properties .

COPY services/igdb_cache/requirements.txt requirements.txt

ADD services/common common

RUN pip install -r requirements.txt

ENV DOCKER_CONTAINER 1

CMD ["python", "./igdb_cache.py"]

