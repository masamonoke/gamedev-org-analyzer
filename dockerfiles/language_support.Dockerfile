FROM python:3.10

ADD services/language_support/language_support.py services/secret.properties .

COPY services/language_support/requirements.txt requirements.txt

ADD services/common common

RUN pip install -r requirements.txt

EXPOSE 12003

ENV DOCKER_CONTAINER 1

CMD ["python", "./language_support.py"]

