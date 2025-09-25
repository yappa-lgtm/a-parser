FROM python:3.12.6-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --upgrade pip wheel "poetry==1.8.3"

RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN poetry install

COPY app .

RUN chmod +x prestart.sh
RUN chmod +x run

ENTRYPOINT ["./prestart.sh"]

CMD ["./run"]