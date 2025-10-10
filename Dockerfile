FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/

RUN apt update -y && \
    apt install -y ruby-full python3-venv && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --break-system-packages -r requirements.txt && \
    gem install taskjuggler

COPY . /app

EXPOSE 8080

CMD ["uvicorn", "http_api.endpoints:app", "--reload", "--port", "8080", "--host", "0.0.0.0"]
