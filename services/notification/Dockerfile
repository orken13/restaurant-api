FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir aio-pika
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]