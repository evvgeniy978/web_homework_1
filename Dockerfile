FROM python:3.13-slim

# Встановлення bash
RUN apt-get update && apt-get install -y bash

WORKDIR /app

COPY . /app

RUN pip install poetry

RUN poetry install --no-root

CMD ["poetry", "run", "python", "web_exercise_02.py"]