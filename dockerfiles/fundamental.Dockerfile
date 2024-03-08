FROM python:3.10

ADD services/fundamental/fundamental.py services/secret.properties .

COPY services/fundamental/requirements.txt requirements.txt

ADD services/common common

RUN pip install -r requirements.txt

EXPOSE 12004

ENV DOCKER_CONTAINER 1

CMD ["python", "./fundamental.py"]

