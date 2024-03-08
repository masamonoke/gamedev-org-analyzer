FROM python:3.10

ADD services/redis_cache/redis_cache.py services/secret.properties .

COPY services/redis_cache/requirements.txt requirements.txt

ADD services/common common

RUN pip install -r requirements.txt

ENV DOCKER_CONTAINER 1

CMD ["python", "./redis_cache.py"]
