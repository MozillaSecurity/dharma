FROM python:3-slim
LABEL maintainer Christoph Diehl <cdiehl@mozilla.com>
ENV PYTHONUNBUFFERED 1
COPY . /app
WORKDIR /app
RUN python setup.py install
ENTRYPOINT [ "dharma" ]
