FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN  apt-get -y update \
     && apt-get install -y \
     zip

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "server.py", "-d", "-l"]