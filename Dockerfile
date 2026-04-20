FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY numerology_bot.py .

CMD ["python", "numerology_bot.py"]
