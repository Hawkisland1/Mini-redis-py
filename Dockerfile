FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY protocol.py server.py client.py main.py ./

EXPOSE 31337

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]