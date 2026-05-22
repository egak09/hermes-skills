# BlockBeats API 完全指南

> BlockBeats Pro API 覆盖 1500+ 信息源，
> 包括 AI 驱动洞察、Hyperliquid 链上数据、Polymarket 市场分析。

---

## 1. API 基础

```
Base URL: https://api-pro.theblockbeats.info
Auth: Header api-key: $BLOCKBEATS_API_KEY
Response: {"status": 0, "message": "", "data": {...}}
         status 0 = 成功
```

### GFW 下的使用

在中国大陆，必须通过代理访问：

```python
import requests

# 不依赖 curl，用 Python requests + 代理
proxies = {
    'http': 'http://127.0.0.1:1081',
    'https': 'http://127.0.0.1:1081',
}
resp = requests.get(url, headers={'api-key': key}, proxies=proxies)
```

> **重要**: API Key 永远从 `.env` 读取，不要依赖 memory。Memory 可能存储了截断或过期的 key。

---

## 2. 七大场景速查

### 场景 1: 市场概览

| 端点 | 指标 | 解读规则 |
|------|------|---------|
| `bottom_top_indicator` | 抄底逃顶情绪 | <20=潜在买入 / 20-80=中性 / >80=潜在卖出 |
| `btc_etf` | BTC ETF 净流入 | 连续3天正=机构积累 / >500M/天=强买入 |
| `daily_tx` | 链上交易量 | 上升=市场热度和活跃度增加 |
| `newsflash/important` | 重要快讯 | 实时事件驱动 |

### 场景 2: 资金流分析

| 端点 | 参数 | 说明 |
|------|------|------|
| `top10_netflow` | `network=solana/base/ethereum` | Top10 净流入代币 |
| `stablecoin_marketcap` | — | USDT/USDC 市值变化 → 资金量 |

### 场景 3: 宏观环境

| 端点 | 参数 | 关键阈值 |
|------|------|---------|
| `m2_supply` | `type=1Y` | YoY>5%=宽松利好 / YoY<0%=紧缩警惕 |
| `us10y` | `type=1M` | 上升=资金回流债券 |
| `dxy` | `type=1M` | 上升=强美元打压加密 |
| `compliant_total` | — | 合规交易所资产总量 |

### 场景 4: 衍生品市场

| 端点 | 参数 |
|------|------|
| `contract` | `dataType=1D/1W/1M` |
| `exchanges` | 交易所排名 |
| `bitfinex_long` | `symbol=btc` `type=h24/1D` |

### 场景 5: 关键词搜索

```bash
GET /v1/search?name=bitcoin&size=10&lang=cn
```

### 场景 6: 快讯 & 文章

| 分类 | 端点 |
|------|------|
| 重要 | `/v1/newsflash/important` |
| 原创 | `/v1/newsflash/original` |
| 链上 | `/v1/newsflash/onchain` |
| 融资 | `/v1/newsflash/financing` |
| AI | `/v1/newsflash/ai` |
| 预测市场 | `/v1/newsflash/prediction` |
| 24小时全量 | `/v1/newsflash/24h` |

---

## 3. 数据刷新频率

| 类型 | 频率 |
|------|------|
| 快讯/文章/搜索 | 实时 |
| top10_netflow | 准实时 |
| btc_etf / daily_tx | 每日 (T+1) |
| stablecoin / 交易所资产 | 每日 |
| 情绪指标 | 每日 |
| 美债/DXY | 分钟级 |
| M2 | 月度 |
| 合约 OI | 每日 |

---

## 4. 错误处理速查

| status | 含义 | 处理 |
|--------|------|------|
| 0 | 成功 | ✅ |
| 100 | 缺少 API key | 检查 header |
| 101 | 无效 key | 重新从 .env 读取 |
| 102 | Key 过期 | 续费 |
| 103 | 请求方法错误 | 确认用 GET |
| -1 | 通用失败 | 查看 message |

---

## 5. 我的实践

### 三个自动化作业

1. **每日简报** (12:00) → `article_fetcher.py` → 深度文章
2. **链上热点** (每4h) → `hotspot_sniper.py` → Base+ETH 净流入
3. **玄学日报** (10:00) → 独立 Python 脚本

### 数据采集脚本模式

```python
# 并行请求多个端点
import requests
from concurrent.futures import ThreadPoolExecutor

def fetch_all(endpoints):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(fetch_one, endpoints))
    return results
```

---

## 6. Paradigme 的内容风格

当为 Paradigme 生成内容时，不是做市场报告：

- ✅ 第一人称，口语化中文，有情绪
- ✅ 像交易者自言自语
- ✅ 不要"非交易建议"等免责声明
- ✅ 4段式：洞察 → 发帖建议 → 数据 → 延伸
- ✅ 发帖建议 tweet-ready（150-280字）
- ❌ 不是客观市场报告
- ❌ 不要"市场概览"标题
- ❌ 不要中性语气

---

### 下一步

→ [02 · 内容自动化流水线](02-content-automation.md)
