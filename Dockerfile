FROM focker.ir/python:3.11-slim


WORKDIR /app
COPY . /app


RUN apt-get -y update && apt-get install -y python
RUN pip install -r requirements.txt
RUN apt-get install gem
RUN gem install taskjuggler

EXPOSE 8080

CMD ["uvicorn", "main:app", "--reload", "--port 8080"]