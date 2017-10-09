FROM python:2.7

WORKDIR /opt/sca/imagex-import

RUN apt-get update && apt-get install -y \
        libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev \
        liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev python-tk

ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

RUN git clone https://github.com/openzoom/deepzoom.py.git /tmp/deepzoom
RUN python /tmp/deepzoom/setup.py install

COPY . .
RUN python watcher.py