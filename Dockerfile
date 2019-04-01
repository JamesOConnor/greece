FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN apt-get install python3

RUN add-apt-repository ppa:ubuntugis/ppa
RUN apt-get update

RUN apt-get install -y gdal-bin

RUN apt-get install -y python3-pip

RUN apt-get install -y gunicorn3
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

ADD . /app
WORKDIR /app

EXPOSE 8000

CMD ["gunicorn3", "wsgi:application", "-c", "gunicorn.conf.py"]