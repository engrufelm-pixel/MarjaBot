FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persistent volume для SQLite базы данных
RUN mkdir -p /app/data && chmod 777 /app/data
ENV DATA_DIR=/app/data

CMD ["python", "bot.py"]
