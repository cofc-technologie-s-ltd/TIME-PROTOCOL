FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000 9201 9202 9203

CMD ["uvicorn", "time_api:app", "--host", "0.0.0.0", "--port", "8000"]
