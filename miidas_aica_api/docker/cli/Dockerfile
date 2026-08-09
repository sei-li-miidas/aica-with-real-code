FROM golang:1.26.5-alpine AS builder

COPY docker/files/ca/Cloudflare_Gateway_CA.pem /usr/local/share/ca-certificates/Cloudflare_Gateway_CA.crt

RUN update-ca-certificates

WORKDIR /go/src/aica

COPY src/ .

RUN go mod download

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /go/bin/batch cli/main.go

FROM alpine:latest

RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

COPY --from=builder /go/bin/batch /usr/local/bin/batch

RUN chown appuser:appgroup /usr/local/bin/batch

USER appuser

ENTRYPOINT ["/usr/local/bin/batch"]
