FROM python:3.10

ADD services/modality/modality.py services/secret.properties .

COPY services/modality/requirements.txt requirements.txt

ADD services/common common

RUN pip install -r requirements.txt

EXPOSE 12002

ENV DOCKER_CONTAINER 1

CMD ["python", "./modality.py"]

