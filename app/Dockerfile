FROM python:3.6

EXPOSE 8080

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app
CMD export FLASK_APP=app.py
CMD flask run --host=0.0.0.0 --port=8080