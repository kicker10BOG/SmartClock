FROM python:3.9-bullseye
LABEL version="0.1"

WORKDIR /app

COPY requirements.txt requirements.txt 
RUN pip3 install -r requirements.txt

EXPOSE 8880

COPY . .
ENTRYPOINT ["python3", "SmartClock.py"]