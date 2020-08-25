FROM python:3.7.4-alpine

RUN apk update && \
    apk add --no-cache --virtual build-deps python-dev postgresql-dev git python3-dev gcc musl-dev \
        jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev \
        tiff-dev tk-dev tcl-dev harfbuzz-dev fribidi-dev

RUN pip3 install --upgrade pip setuptools \
    && wget -qO- https://github.com/jwilder/dockerize/releases/download/v0.2.0/dockerize-linux-amd64-v0.2.0.tar.gz | tar -zxf - -C /usr/bin \
    && chown root:root /usr/bin/dockerize

WORKDIR /opt/

ENV DJANGO_SETTINGS_MODULE=paul_api.settings

# Copy just the requirements for caching
COPY ./requirements* /opt/
RUN pip3 install -r requirements.txt

WORKDIR /opt/paul_api/

COPY ./docker/api/docker-entrypoint /
COPY ./ /opt/

ENTRYPOINT ["/docker-entrypoint"]
EXPOSE 8000