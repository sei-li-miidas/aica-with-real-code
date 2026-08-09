# Build stage
ARG NODE_VERSION=22.22.0
ARG DEBIAN_VERSION=trixie
FROM node:${NODE_VERSION}-${DEBIAN_VERSION}-slim AS builder

ENV NEXT_TELEMETRY_DISABLED=1

ARG NEXT_PUBLIC_AGENT_ENDPOINT
ARG NEXT_PUBLIC_API_ENDPOINT
ARG NEXT_PUBLIC_BASE_PATH
ARG NEXT_PUBLIC_ASSET_PATH
ARG NEXT_PUBLIC_APP_ENV
ARG NEXT_PUBLIC_GTM_TRACKING_CODE
ENV NEXT_PUBLIC_AGENT_ENDPOINT=${NEXT_PUBLIC_AGENT_ENDPOINT}
ENV NEXT_PUBLIC_API_ENDPOINT=${NEXT_PUBLIC_API_ENDPOINT}
ENV NEXT_PUBLIC_BASE_PATH=${NEXT_PUBLIC_BASE_PATH}
ENV NEXT_PUBLIC_ASSET_PATH=${NEXT_PUBLIC_ASSET_PATH}
ENV NEXT_PUBLIC_APP_ENV=${NEXT_PUBLIC_APP_ENV}
ENV NEXT_PUBLIC_GTM_TRACKING_CODE=${NEXT_PUBLIC_GTM_TRACKING_CODE}

WORKDIR /app
COPY package*.json ./
RUN npm ci --ignore-scripts --min-release-age=7

COPY . .
RUN npm run build

# Deploy stage
FROM nginx:stable-${DEBIAN_VERSION}
ENV LANG ja_JP.UTF-8
LABEL maintainer="MIIDAS Team <miidasteam@docker.miidas.jp>"

COPY ./docker/ecs/nginx/nginx/ /etc/nginx/
COPY ./docker/ecs/nginx/tmp/ /tmp/

COPY --from=builder /app/build/ /var/www/html/miidas_aica_frontend/public/aica/

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/* && \
    chmod u+x /tmp/*.sh
