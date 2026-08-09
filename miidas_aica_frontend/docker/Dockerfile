# Build stage
ARG NODE_VERSION=22.22.0
ARG DEBIAN_VERSION=trixie
FROM node:${NODE_VERSION}-${DEBIAN_VERSION}-slim AS builder

WORKDIR /app

COPY . .
RUN rm -rf /app/node_modules
RUN rm -rf /app/build

RUN npm ci --ignore-scripts --min-release-age=7
RUN npm run build

# Deploy stage
FROM nginx:alpine

COPY --from=builder /app/build /var/www/aica

COPY docker/rootfs/etc/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/rootfs/etc/nginx/conf.d /etc/nginx/conf.d

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
