FROM python:3.8-slim AS build-image
MAINTAINER David Yu <guanshan@gmail.com>

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc


# install pip packages
RUN set -xe \
    && pip install --upgrade pip \
    && pip install pipenv

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" VIRTUAL_ENV="/opt/venv"

COPY Pipfile Pipfile.lock /opt/app/
WORKDIR /opt/app
RUN pipenv install --deploy --ignore-pipfile



FROM python:3.8-slim AS deploy-image
WORKDIR /opt/app
COPY --from=build-image /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" VIRTUAL_ENV="/opt/venv" PYTHONPATH="/opt/app"
COPY . /opt/app/
EXPOSE 8000

CMD ["python", "idiomfinder/main.py"]