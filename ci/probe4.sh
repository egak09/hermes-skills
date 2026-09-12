#!/usr/bin/env bash
# 探测币安公告 API（上币历史金矿）
set -uo pipefail
W="${WORKER_URL:-https://http-proxy.skyproxy2026.workers.dev}"
OUT="mexc/data/probe4"
mkdir -p "$OUT"
enc() { jq -rn --arg v "$1" '$v|@uri'; }

g() { # name  target_url [via_worker]
  local name="$1" target="$2" via="${3:-direct}"
  local code
  if [ "$via" = "worker" ]; then
    code=$(curl -sS -m 60 -o "$OUT/$name.json" -w '%{http_code}' "$W/?url=$(enc "$target")" 2>/dev/null || echo ERR)
  else
    code=$(curl -sS -m 60 -o "$OUT/$name.json" -w '%{http_code}' "$target" \
      -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
      -H "Accept: application/json" 2>/dev/null || echo ERR)
  fi
  local size; size=$(wc -c < "$OUT/$name.json" 2>/dev/null || echo 0)
  echo "[$name/$via] HTTP=$code bytes=$size"
  jq -c 'if type=="object" then (.data|if type=="array" then {n:(length), sample:(.[0]|tostring|.[0:120])} elif type=="object" then (to_entries|map(.key)|.[0:12]) else . end) else {type:(type)} end' "$OUT/$name.json" 2>/dev/null | head -c 400
  echo
}

echo "===== 1. 币安公告 目录清单 ====="
g 01-catalogs "https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query?type=1"

echo "===== 2. 上币公告列表（catalogId=48 新币上线）====="
g 02-articles-48-p1 "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=50&catalogId=48"
g 03-articles-48-p2 "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=2&pageSize=50&catalogId=48"

echo "===== 3. 其他相关目录（合约上线等）====="
g 04-articles-49-p1 "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20&catalogId=49"
g 05-articles-93-p1 "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20&catalogId=93"

echo "===== 4. 现货/合约 exchangeInfo（经 www.binance.com）====="
g 06-spot-exchangeinfo-www "https://www.binance.com/api/v3/exchangeInfo"
g 07-fapi-exchangeinfo-www "https://www.binance.com/fapi/v1/exchangeInfo"
g 08-products "https://www.binance.com/bapi/asset/v2/public/asset-service/product/get-products"

echo "===== 5. 经 Worker 是否也能访问 www.binance.com ====="
g 09-worker-announcements "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=10&catalogId=48" worker

echo "===== 完成 ====="
du -sh "$OUT"; ls -la "$OUT" | head -20
