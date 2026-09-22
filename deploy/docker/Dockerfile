FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir cryptography

EXPOSE 8080 9091

CMD ["python", "scripts/run_cluster.py"]
