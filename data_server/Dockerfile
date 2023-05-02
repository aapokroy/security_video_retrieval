FROM python:3.10.11-slim-buster
WORKDIR /app
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && apt-get install ffmpeg libsm6 libxext6  -y
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
COPY secrets /secrets
CMD ["python", "-m", "app"]