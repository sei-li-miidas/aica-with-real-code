#!/bin/sh

# 単純な環境変数の展開は envsubst で行い、その他の設定は include 用のファイルで行う
envsubst '$MIIDAS_DOMAIN_AICA_MCP_LOCAL $MIIDAS_DOMAIN_AICA_MCP_LOCAL_OLD' \
  < /etc/nginx/templates/miidas_aica_mcp.conf.tmpl > /etc/nginx/conf.d/miidas_aica_mcp.conf

exec nginx -g 'daemon off;'
