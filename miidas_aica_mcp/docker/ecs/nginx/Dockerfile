FROM nginx:stable-trixie
ENV LANG ja_JP.UTF-8
LABEL maintainer="MIIDAS Team <miidasteam@docker.miidas.jp>"

COPY ./nginx/ /etc/nginx/
COPY ./tmp/ /tmp/

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/* && \
    chmod u+x /tmp/*.sh
