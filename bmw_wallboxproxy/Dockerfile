ARG BUILD_FROM=ghcr.io/home-assistant/base:latest
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip

WORKDIR /app

COPY requirememts.txt /app/requirememts.txt
RUN pip3 install --no-cache-dir -r /app/requirememts.txt

COPY . /app/

RUN chmod a+x /run.sh

CMD ["/run.sh"]