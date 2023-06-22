FROM ubuntu:latest
WORKDIR /usr/src/app
COPY ./ ./
RUN DEBIAN_FRONTEND=noninteractive \
apt update && \
apt install -yq --no-install-recommends python3 python3-requests python3-pytest && \
rm -rf /var/lib/apt/lists/* && \
apt clean
ENTRYPOINT 'pytest-3'