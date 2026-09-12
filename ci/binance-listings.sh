#!/usr/bin/env bash
# 全量抓取币安上币公告（catalogId=48 "New Cryptocurrency Listing"）
# 数据源：https://www.binance.com/bapi/composite/v1/public/cms/article/list/query
# 返回字段：id / code / title / releaseDate(ms)  —— 精确到毫秒，可回溯至 2017
set -uo pipefail

OUT="mexc/data/binance-announcements"
RAW="$OUT/raw"
mkdir -p "$RAW"

PS=50          # 每页条数
MAXPAGE=60     # 安全上限

API="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=48"

echo "开始抓取币安上币公告..."
: > "$OUT/pagecounts.txt"
for p in $(seq 1 $MAXPAGE); do
  f="$RAW/page-$(printf '%03d' "$p").json"
  code=$(curl -sS -m 60 -o "$f" -w '%{http_code}' \
    "$API&pageNo=$p&pageSize=$PS" \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36" \
    -H "Accept: application/json" 2>/dev/null || echo ERR)

  n=$(jq -r '.data.catalogs[0].articles | length' "$f" 2>/dev/null || echo 0)
  total=$(jq -r '.data.catalogs[0].total' "$f" 2>/dev/null || echo 0)
  echo "page $p HTTP=$code articles=$n (catalog total=$total)"
  echo "$p $n $total" >> "$OUT/pagecounts.txt"

  if [ "$n" = "0" ] || [ -z "$n" ] || [ "$n" = "null" ]; then
    echo "→ 第 $p 页为空，停止"
    break
  fi
  sleep 0.7   # 温和限速
done

echo
echo "===== 合并 ====="
jq -s '[.[].data.catalogs[0].articles[]?] | unique_by(.id) | sort_by(.releaseDate)' \
   "$RAW"/page-*.json > "$OUT/articles.json" 2>/dev/null || echo "合并失败"

COUNT=$(jq 'length' "$OUT/articles.json" 2>/dev/null || echo 0)
echo "合并后公告数: $COUNT"

echo "===== 导出 CSV ====="
jq -r '(["id","release_date_ms","release_date_utc","title","code"] | @csv),
       (.[] | [.id, .releaseDate,
               (.releaseDate/1000 | strftime("%Y-%m-%d %H:%M:%S")),
               .title, .code] | @csv)' \
   "$OUT/articles.json" > "$OUT/articles.csv" 2>/dev/null || echo "CSV 导出失败"

wc -l "$OUT/articles.csv" 2>/dev/null
head -3 "$OUT/articles.csv" 2>/dev/null
echo "===== 完成 ====="
