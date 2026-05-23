# Hermes 运维笔记：Cron 调试 + C盘瘦身实战

**日期**：2026-05-23  
**标签**：#hermes #cron #windows #disk-cleanup

---

## 一、Cron Job 静默失败排查

### 现象
每日加密简报 cron（12:00 HKT）调度器显示 `status: ok`，但 Telegram 收不到推送，session 数据库也无记录。

### 排查路径
1. `cronjob list` → 确认 job 触发时间、状态均为正常
2. `session_search` → 目标 session 不存在（不是没推送，是根本没生成）
3. 手动跑 `article_fetcher.py` → 输出 **56KB+** 完整 HTML 正文

### 根因
脚本输出过于庞大（5篇重要文章+5篇原创+24h全部文章，每篇完整 HTML），注入 LLM 上下文后直接撑爆 token 上限 → Agent 崩溃 → 无 session → 无推送。

调度器层面只关心"脚本是否正常退出"，脚本确实正常退出 → `status: ok`。但 Agent 还没来得及生成回复就挂了。

### 修复
```python
# article_fetcher.py 改动三处：
# 1. 去掉 content 字段，只保留 title/description/link/time
# 2. 文章数：5+5+50 → 3+3+10
# 3. 新增 strip_articles() 递归清洗函数

def strip_articles(data):
    if isinstance(data, dict) and "data" in data:
        data["data"] = [strip_articles(item) for item in data["data"]]
        return data
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k not in ("content", "is_original")}
    return data
```

> 效果：56KB → 6.5KB（压缩 88%）

### 教训
- Cron 脚本输出要精打细算——每多 1KB 都是和 token 预算抢空间
- `last_status: ok` ≠ "成功推送"。脚本 exit code 和 Agent 输出是两个独立环节
- 脚本层面做数据瘦身，比靠 LLM prompt 控制更可靠

---

## 二、Windows C盘深度瘦身

### 工具链
- `windows-disk-cleanup` skill：scan.py + clean.py
- 核心思路：先扫描 → 排名 → 确认 → 清理，不留后患

### 清理节奏（四轮）

| 轮次 | 目标 | 大小 | 备注 |
|------|------|------|------|
| 1 | Temp + Chrome/Edge缓存 + 缩略图 | 1.9 GB | 安全项，一键清 |
| 2 | Lark（飞书国际版） | ~3.5 GB | 和 Feishu 重复安装，双飞书吃了 6.7G |
| 3 | WSL Ubuntu | ~1.5 GB | Hermes 不用 WSL（backend: local） |
| 4 | Minecraft + Isaac | ~6.5 GB | 游戏在 AppData 里，不在 Steam 目录 |
| 🔒 | 8项 Program Files 顽固 | ~3.4 GB | 需管理员权限 |

### 收益
```
132.2 GB → 114.0 GB  （91% → 78.4%）
释放 18.2 GB，剩余 31.4 GB
```

### 技巧总结
1. **Python 扫描比 bash `du` 快得多**——Windows 上 `du -sh` 对大目录直接超时
2. **AppData 是隐形大户**：Local 9.5G + Roaming 6G = 15.5G
3. **双飞书（Lark + Feishu）** 是最蠢的空间浪费——同款软件两个版本吃 6.7G
4. **Program Files 清理需要 admin**：`rm -rf` → Permission denied，PowerShell `Remove-Item` 一样
5. **进程锁文件**：Lark 后台进程锁着 400MB 数据库，需要先 `taskkill` 再 `rm`

### 常见垃圾位置速查
- `%LOCALAPPDATA%\Temp` — 2GB 级
- `%APPDATA%\.minecraft` — 6GB 级
- `%LOCALAPPDATA%\Lark` / `Feishu` — 3GB 级
- `%LOCALAPPDATA%\wsl` — 1.5GB 级
- `C:\Program Files\NVIDIA Corporation` — 驱动残留

---

## 三、今日一句话

> Cron 脚本的输出不是给人类看的，是给 LLM 吃的。每多 1KB 都是在赌 token 天花板不会砸下来。
