# 内容自动化流水线

> 从数据到内容的完整自动化链路：采集 → 加工 → 推送

---

## 1. 流水线架构

```
Python 数据采集 → LLM Agent 范式化加工 → Telegram 推送
   脚本负责            Agent负责              Gateway负责
   API调用             叙事+风格              投递
   JSON解析            格式化                 展示
```

### 为什么脚本 + Agent？

| 纯脚本 | 纯 Agent | 脚本 + Agent |
|--------|---------|-------------|
| 输出僵硬 | API 调用慢 | 脚本快+并行 |
| 无法叙事 | Token 成本高 | Agent 负责叙事 |
| 需人工格式化 | 不适合大批量 | 分工明确 |

---

## 2. 三个采集脚本

### article_fetcher.py — 每日深度文章

```python
# 并行调用三个端点
endpoints = [
    '/v1/article/important',   # 重要文章
    '/v1/article/original',    # 原创分析
    '/v1/article/24h',         # 24h 全量
]
```

### hotspot_sniper.py — 链上热点狙击

```python
# Base + Ethereum 两条链的 Top10 净流入
networks = ['base', 'ethereum']

# v2 升级：每个热点币追加关键词搜索
for coin in top_coins:
    narrative = search_news(keyword=coin.symbol)
```

### daily_briefing.py — 全维度日报

```python
# 7 个端点并行
endpoints = [
    'sentiment', 'important_news', 'btc_etf',
    'daily_tx', 'ai_news', 'top10_netflow', 'stablecoin'
]
```

---

## 3. Cron → Agent → Push 完整链路

### 时间线

```
12:00 — Cron 触发
12:00 — article_fetcher.py 运行（~15 秒）
12:00 — 脚本输出 JSON 注入 Agent prompt
12:00 — Agent 用 Paradigme 风格格式化
12:00 — Gateway 推送到 Telegram
```

### Cron Job 配置要点

```python
cronjob(action='create',
    name='每日加密简报 12:00',
    schedule='0 12 * * *',
    script='article_fetcher.py',
    skills=['blockbeats-skill'],
    deliver='origin',
    # prompt 字段为完整的自包含任务指令
    # Cron 运行无对话上下文，prompt 必须写清楚风格和格式
)
```

---

## 4. 关键约束

| 约束 | 说明 |
|------|------|
| 脚本路径 | 必须相对于 `~/.hermes/scripts/`（不能用绝对路径） |
| Python 环境 | Cron 用系统 Python，不是 MSYS2 的 |
| 代理 | 脚本内硬编码 `http://127.0.0.1:1081` |
| no_agent | 留默认 false（需要 LLM 叙事加工） |
| 推送 | `deliver='origin'` → Telegram DM |

---

## 5. 内容策略矩阵

| 频次 | 内容类型 | 脚本 | 风格 |
|------|---------|------|------|
| 每日 | 深度洞察 | article_fetcher | 交易心理+发帖建议 |
| 每 4h | 热点狙击 | hotspot_sniper | 链上数据+叙事研究 |
| 每日 | 玄学辅助 | 独立脚本 | 八字+紫微+星盘 |

---

### 回到总览

→ [README.md](README.md)
