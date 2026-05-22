# Cron 自动化：让 Agent 自己运转

> Hermes 内置的 cron 调度器可以定时自动运行 Agent——  
> 不需要人盯着，Agent 会自动采集数据、分析、推送。

---

## 1. 我的三个 Cron Job

### 🔮 玄学日报（每天 10:00）

```yaml
调度: 0 10 * * *
Skill: esoteric-daily-guidance
功能: 八字+紫微+星盘三合一每日推演
```

### 📊 加密简报（每天 12:00）

```yaml
调度: 0 12 * * *
Skill: blockbeats-skill
脚本: article_fetcher.py（数据采集）
功能: BlockBeats 数据 → Paradigme 风格日报
```

### 🔍 链上热点狙击（每 4 小时）

```yaml
调度: 0 */4 * * *
Skill: blockbeats-skill  
脚本: hotspot_sniper.py（热点采集）
功能: Base + Ethereum Top10 净流入代币
```

---

## 2. Cron 作业的完整流水线

```
┌─────────────┐      ┌─────────────┐      ┌──────────────┐
│ 脚本采集数据  │  →  │ LLM 加工分析  │  →  │ 推送到 Telegram │
│ (Python)    │      │ (Agent 推理)  │      │ (Gateway)      │
└─────────────┘      └─────────────┘      └──────────────┘
     ↑                                            │
     └──────────── 每 N 小时/天 循环 ─────────────┘
```

### 脚本 vs Agent 的分工

| 环节 | 谁负责 | 为什么 |
|------|--------|--------|
| API 调用、JSON 解析 | Python 脚本 | 快、稳定、可并行 |
| 数据格式化、叙事生成 | LLM Agent | 需要推理和文字能力 |
| 推送、调度 | Hermes Cron | 内置能力 |

---

## 3. 创建 Cron Job 的关键参数

```python
cronjob(action='create',
    name='任务名',
    schedule='0 12 * * *',     # cron 表达式
    script='collector.py',     # 采集脚本（相对 ~/.hermes/scripts/）
    skills=['blockbeats-skill'], # 加载的 skill
    prompt='完整的任务指令...',  # 自包含（cron 无对话上下文）
    deliver='origin',          # 推送到 Telegram
    no_agent=False,            # False=LLM加工, True=脚本输出直推
)
```

### ⚠️ 关键约束

1. **脚本路径必须是相对路径**：`script='foo.py'` → 解析为 `~/.hermes/scripts/foo.py`
2. **Prompt 必须自包含**：cron 运行时没有对话历史
3. **no_agent 场景区分**：
   - `False`（默认）：脚本采集数据 → LLM 格式化 → 推送（适合需要叙事加工的）
   - `True`：脚本输出直推，不走 LLM（适合纯数据监控）

---

## 4. Cron Job 的生命周期管理

```bash
# 查看所有
hermes cron list

# 暂停/恢复
hermes cron pause <job_id>
hermes cron resume <job_id>

# 手动触发
hermes cron run <job_id>

# 删除
hermes cron remove <job_id>
```

### Chain Jobs（作业链）

Job B 可以消费 Job A 的输出：

```python
cronjob(action='create', ...,
    context_from=['job_a_id'])  # 注入 Job A 的上次输出
```

---

## 5. 内容创作引擎实战

### 我的加密简报 Prompt 核心

```
你是 Paradigme (@sky_dai7334) 的专属内容创作 Agent

风格要求：
- 第一人称，口语化中文，有情绪
- 像交易者自言自语，不是市场报告
- 不要"非交易建议"等免责声明
- 4段式：核心洞察 → 发帖建议 → 数据要点 → 延伸方向
```

### 数据 → 内容的转化链

```
BlockBeats API（原始 JSON）
    ↓ article_fetcher.py 过滤/聚合
结构化数据摘要
    ↓ LLM Agent（Paradigme 风格）
200-280字可发帖内容 + 交易心理洞察
    ↓ Telegram Gateway
用户收到推送
```

---

## 6. 调度技巧

| 场景 | 推荐频率 | 原因 |
|------|---------|------|
| 市场情绪日报 | 每天 1 次 | 日线级别足够 |
| 链上热点 | 每 4-6 小时 | 热点变化快但不过于频繁 |
| 妖币扫描 | 每 3 分钟 | 需要高频（建议独立进程） |
| 系统监控 | 每 30 分钟 | 磁盘/内存/进程 |

---

### 下一步

→ [04 · 多 Agent 协作](04-multi-agent.md)
