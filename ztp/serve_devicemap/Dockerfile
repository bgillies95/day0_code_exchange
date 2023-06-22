FROM python:3-slim-bullseye
WORKDIR /usr/src/app
COPY app.py ./
RUN DEBIAN_FRONTEND=noninteractive \
apt update && \
apt -yq upgrade && \
apt install -yq --no-install-recommends python3 python3-pip gcc build-essential python-dev && \
python3 -m pip install uwsgi && \
rm -rf /var/lib/apt/lists/* && \
apt clean
EXPOSE 8081
ENTRYPOINT [ "uwsgi", "--http", ":8081", "--wsgi-file", "app.py", \
"--master", "--processes", "4", "--threads", "2", "--stats", "127.0.0.1:8082"]