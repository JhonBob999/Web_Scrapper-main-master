FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    chromium-driver chromium wget curl unzip gnupg \
    && rm -rf /var/lib/apt/lists/*

# ВАЖНО: ставим старую версию blinker
RUN pip install --no-cache-dir selenium selenium-wire blinker==1.4

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER=/usr/bin/chromedriver

WORKDIR /app
COPY entrypoint.py .

CMD ["python", "entrypoint.py"]
