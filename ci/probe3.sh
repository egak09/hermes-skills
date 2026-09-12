#!/usr/bin/env bash
# 探测：哪些通道能拿到币安数据
set -uo pipefail
W="${WORKER_URL:-https://http-proxy.skyproxy2026.workers.dev}"
OUT="mexc/data/probe3"
mkdir -p "$OUT"
enc() { jq -rn --arg v "$1" '$v|@uri'; }

t() { # name  cmd...
  local name="$1"; shift
  local code
  code=$(curl -sS -m 45 -o "$OUT/$name.raw" -w '%{http_code}' "$@" 2>/dev/null || echo ERR)
  {
    echo "HTTP=$code"
    echo "--- body (first 800 bytes) ---"
    head -c 800 "$OUT/$name.raw" 2>/dev/null
    echo
  } > "$OUT/$name.txt"
  echo "[$name] HTTP=$code :: $(head -c 160 "$OUT/$name.raw" 2>/dev/null | tr -d '\n')"
  rm -f "$OUT/$name.raw"
}

BINANCE_SPOT="https://api.binance.com/api/v3/ping"
BINANCE_FAPI="https://fapi.binance.com/fapi/v1/ping"
BINANCE_VISION="https://data-api.binance.vision/api/v3/ping"

echo "===== 0. runner 直连（确认 runner 地区限制）====="
t 00-runner-direct-spot "$BINANCE_SPOT"
t 00b-runner-ip "https://api.ipify.org"

echo "===== 1. 公共 CORS 代理 ====="
t 10-allorigins-spot  "https://api.allorigins.win/raw?url=$(enc "$BINANCE_SPOT")"
t 11-codetabs-spot    "https://api.codetabs.com/v1/proxy?quest=$(enc "$BINANCE_SPOT")"
t 12-corsproxy-spot   "https://corsproxy.io/?$(enc "$BINANCE_SPOT")"
t 13-thingproxy-spot  "https://thingproxy.freeboard.io/fetch/$BINANCE_SPOT"
t 14-jina-spot        "https://r.jina.ai/$BINANCE_SPOT"
t 15-allorigins-fapi  "https://api.allorigins.win/raw?url=$(enc "$BINANCE_FAPI")"
t 16-allorigins-vis   "https://api.allorigins.win/raw?url=$(enc "$BINANCE_VISION")"

echo "===== 2. Worker 节点信息 + MCP(Bearer) ====="
t 20-worker-cf-trace  "$W/?url=$(enc "https://api.cryptorank.io/v3/status")"
MCP="https://api.cryptorank.io/mcp"
t 21-mcp-bearer-curl  -X POST "$W/?url=$(enc "$MCP")" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

echo "===== 3. 其他可行代理（非 CF 区域）====="
t 30-npoint-spot      "https://api.cors.lol/?url=$(enc "$BINANCE_SPOT")"
t 31-proxysite-spot   "https://api.scrape.do/?url=$(enc "$BINANCE_SPOT")"
t 32-whateverorigin   "http://www.whateverorigin.org/get?url=$(enc "$BINANCE_SPOT")"
t 33-textance         "https://r.jina.ai/https://api.binance.com/api/v3/exchangeInfo"

echo "===== 4. 币安备用域名 ====="
t 40-binance-com-ping  "https://www.binance.com/api/v3/ping"
t 41-binance-us        "https://api.binance.us/api/v3/ping"
t 42-binance-tr        "https://www.binance.tr/api/v3/ping"

echo "===== 完成 ====="
