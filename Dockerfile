FROM python:2.7.14-jessie

RUN apt-get update && apt-get install -y \
        libtiff5-dev libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev

ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt
RUN pip install pyfits==3.4

RUN git clone https://github.com/openzoom/deepzoom.py.git /tmp/deepzoom
WORKDIR /tmp/deepzoom
RUN python setup.py install

WORKDIR /opt/sca/imagex-importer
COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/opt/sca/config/"

CMD ["python", "watcher.py"]