FROM focker.ir/ubuntu:latest

WORKDIR /app

COPY requirements.txt /app/
RUN apt update -y && \
    apt install -y python3 python3-pip python3-venv ruby-full && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --break-system-packages -r requirements.txt
RUN gem install taskjuggler

EXPOSE 8080

CMD ["uvicorn", "main:app", "--reload", "--port", "8080", "--host", "0.0.0.0"]
