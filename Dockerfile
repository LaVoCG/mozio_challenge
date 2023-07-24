FROM python:3.8

ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get install libffi-dev
RUN pip install poetry

WORKDIR /app
COPY . /app

COPY poetry.lock pyproject.toml /app/

RUN poetry install --no-interaction

#COPY . /app
VOLUME /app

CMD ["poetry", "run", "flask", "--app", "./mozioapi/mozioapi", "run", "--host=0.0.0.0"]
