#!/usr/bin/env bash
# 数据源可达性探测 —— 经 Cloudflare Worker 代理
set -uo pipefail

W="${WORKER_URL:-https://http-proxy.skyproxy2026.workers.dev}"
OUT="mexc/data/probe2"
mkdir -p "$OUT"

enc() { jq -rn --arg v "$1" '$v|@uri'; }

probe() {  # name  target_url
  local name="$1" target="$2"
  local e code
  e=$(enc "$target")
  code=$(curl -sS -m 60 -o "$OUT/$name.raw" -w '%{http_code}' "$W/?url=$e" 2>/dev/null || echo "ERR")
  local size
  size=$(wc -c < "$OUT/$name.raw" 2>/dev/null || echo 0)
  echo "[$name] HTTP=$code bytes=$size <- $target"
  head -c 400 "$OUT/$name.raw" > "$OUT/$name.txt" 2>/dev/null
  rm -f "$OUT/$name.raw"
}

echo "===== A. 币安 API 可达性 ====="
probe a1-fapi-ping        "https://fapi.binance.com/fapi/v1/ping"
probe a2-spot-ping        "https://api.binance.com/api/v3/ping"
probe a3-vision-ping      "https://data-api.binance.vision/api/v3/ping"
probe a4-fapi-exchangeinfo "https://fapi.binance.com/fapi/v1/exchangeInfo"
probe a5-spot-exchangeinfo "https://api.binance.com/api/v3/exchangeInfo"

echo "===== B. 其他数据源 ====="
probe b1-coingecko-ping   "https://api.coingecko.com/api/v3/ping"
probe b2-llama-protocols  "https://api.llama.fi/protocols"
probe b3-mexc-ping        "https://api.mexc.com/api/v3/ping"
probe b4-okx-instruments  "https://www.okx.com/api/v5/public/instruments?instType=SPOT"

echo "===== C. CryptoRank 可用端点 ====="
probe c1-cr-currencies   "https://api.cryptorank.io/v3/currencies/list?limit=2"
probe c2-cr-exchanges    "https://api.cryptorank.io/v3/exchanges/map"
probe c3-cr-categories   "https://api.cryptorank.io/v3/currencies/categories"
probe c4-cr-global       "https://api.cryptorank.io/v3/global/market"
probe c5-cr-binance-mkts "https://api.cryptorank.io/v3/exchanges/binance/markets"
probe c6-cr-listing      "https://api.cryptorank.io/v3/currencies/list?limit=2&orderBy=dateAdded&orderDirection=desc"

echo "===== 完成 ====="
ls -1 "$OUT"
