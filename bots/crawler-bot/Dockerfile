# bots/crawler-bot/Dockerfile

FROM python:3.10-slim

WORKDIR /app

COPY entrypoint.py .

RUN pip install requests beautifulsoup4

CMD ["python", "entrypoint.py"]
