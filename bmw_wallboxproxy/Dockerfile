ARG BUILD_FROM=ghcr.io/home-assistant/base:latest
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip py3-virtualenv

WORKDIR /app

COPY requirememts.txt /app/requirememts.txt
RUN python3 -m venv /opt/venv \
	&& /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
	&& /opt/venv/bin/pip install --no-cache-dir -r /app/requirememts.txt

COPY . /app/

RUN chmod a+x /run.sh

CMD ["/run.sh"]