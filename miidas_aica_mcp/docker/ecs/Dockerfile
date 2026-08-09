# syntax=docker/dockerfile:1
ARG GOLANG_VERSION=1.26.5
ARG DEBIAN_VERSION=trixie

# Golangソースコードをビルド
FROM golang:${GOLANG_VERSION} AS builder
ENV CGO_ENABLED=0

ARG BUILD_COMMIT_HASH
ARG BUILD_TIME
ENV BUILD_LDFLAGS="-s -w"

WORKDIR /go/src/aica
COPY src .
RUN go build -trimpath -ldflags="${BUILD_LDFLAGS}" -o /go/bin/mcpserver main.go

# 実行用イメージをビルド
FROM debian:${DEBIAN_VERSION}-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /usr/local/go/miidas_go/bin
COPY --from=builder /go/bin/mcpserver ./

EXPOSE 8080
