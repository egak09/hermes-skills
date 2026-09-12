#!/usr/bin/env bash
# CryptoRank API 探测 —— 通过 Cloudflare Worker 代理访问
# 运行环境：GitHub Actions runner（不受 GFW 限制）
set -uo pipefail

W="${WORKER_URL:-https://http-proxy.skyproxy2026.workers.dev}"
OUT="mexc/data/cryptorank-probe"
mkdir -p "$OUT"

enc() { jq -rn --arg v "$1" '$v|@uri'; }

get() {  # name  target_url
  local name="$1" target="$2"
  local e code
  e=$(enc "$target")
  code=$(curl -sS -m 60 -o "$OUT/$name.raw" -w '%{http_code}' "$W/?url=$e" 2>"$OUT/$name.err" || echo "ERR")
  local size
  size=$(wc -c < "$OUT/$name.raw" 2>/dev/null || echo 0)
  echo "[$name] HTTP=$code bytes=$size  <- $target"
  # 去掉 X-Proxy 头之外的响应体已是 JSON；美化一下方便阅读
  if jq -e . "$OUT/$name.raw" >/dev/null 2>&1; then
    jq . "$OUT/$name.raw" > "$OUT/$name.json" 2>/dev/null && rm -f "$OUT/$name.raw"
  fi
}

echo "=== worker health ==="
curl -sS -m 30 "$W/" | tee "$OUT/00-worker-health.json"
echo

echo "=== CryptoRank REST 探测 ==="
get 01-status        "https://api.cryptorank.io/v3/status"
get 02-currencies    "https://api.cryptorank.io/v3/currencies?limit=3"
get 03-exchanges     "https://api.cryptorank.io/v3/exchanges?limit=3"
get 04-coins         "https://api.cryptorank.io/v3/coins?limit=3"
get 05-global        "https://api.cryptorank.io/v3/global"
get 06-ico           "https://api.cryptorank.io/v3/ico?limit=3"
get 07-market-pairs  "https://api.cryptorank.io/v3/market-pairs?limit=3"
get 08-categories    "https://api.cryptorank.io/v3/categories?limit=3"
get 09-tickers       "https://api.cryptorank.io/v3/tickers?limit=3"

echo "=== MCP 端点探测 ==="
MCP="https://api.cryptorank.io/mcp"
E=$(enc "$MCP")
for method in "initialize" "tools/list"; do
  fname="10-mcp-$(echo "$method" | tr '/' '-')"
  echo "--- MCP $method ---"
  if [ "$method" = "initialize" ]; then
    BODY='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}'
  else
    BODY='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
  fi
  curl -sS -m 60 -X POST "$W/?url=$E" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d "$BODY" -o "$OUT/$fname.raw" -w "HTTP=%{http_code} bytes=%{size_download}\n" || true
  head -c 1500 "$OUT/$fname.raw" > "$OUT/$fname.txt" 2>/dev/null
  rm -f "$OUT/$fname.raw"
done

echo "=== 文档站 ==="
get 11-docs "https://docs.cryptorank.io/"
echo "=== 完成 ==="
ls -la "$OUT"
