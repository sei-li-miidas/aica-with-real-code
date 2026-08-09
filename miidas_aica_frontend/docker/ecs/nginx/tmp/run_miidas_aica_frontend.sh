#!/bin/sh

# 単純な環境変数の展開は envsubst で行い、その他の設定は include 用のファイルで行う
envsubst '$MIIDAS_DOMAIN_AICA_FRONT $MIIDAS_ASSETS_DOMAIN' \
  < /etc/nginx/templates/miidas_aica_frontend.conf.tmpl > /etc/nginx/conf.d/miidas_aica_frontend.conf

exec nginx -g 'daemon off;'
