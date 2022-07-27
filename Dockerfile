FROM python:3.7.4-alpine

RUN apk update --no-cache && \
    apk add --no-cache --virtual .build-deps python-dev postgresql-dev git python3-dev gcc g++ musl-dev \
        jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev \
        tiff-dev tk-dev tcl-dev harfbuzz-dev fribidi-dev libc-dev

RUN pip3 install --upgrade pip setuptools greenlet cython

COPY --from=jwilder/dockerize:0.6.1 /usr/local/bin/dockerize /usr/local/bin/dockerize



WORKDIR /opt/

ENV DJANGO_SETTINGS_MODULE=paul_api.settings
# mkdir media dir
RUN mkdir -p /var/www/paul-api/media

# Copy just the requirements for caching
COPY ./requirements* /opt/
RUN pip3 install -r requirements.txt

# RUN apk del .build-deps gcc musl-dev g++

WORKDIR /opt/paul_api/

COPY ./docker-entrypoint /
COPY ./ /opt/

ENTRYPOINT ["/docker-entrypoint"]
EXPOSE 8000
