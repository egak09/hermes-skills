# Windows 下 Hermes 运维

---

## 1. Hermes 目录结构

```
C:\Users\<user>\AppData\Local\hermes\
├── config.yaml          # 主配置
├── .env                 # API keys
├── skills/              # 技能（已 Junction → D:）
├── sessions/            # 会话记录（已 Junction → D:）
├── cache/               # 模型缓存（已 Junction → D:）
├── image_cache/         # 图片缓存（已 Junction → D:）
├── audio_cache/         # 音频缓存（已 Junction → D:）
├── cron/                # 定时任务
├── memories/            # 持久记忆
├── logs/                # 日志（被 gateway 锁，未迁移）
├── hermes-agent/        # 源代码（~35K文件，未动）
├── scripts/             # Cron 脚本目录
└── profiles/            # 多 Profile 配置
```

---

## 2. 磁盘迁移：Windows Junction

### 为什么用 Junction？

- Hermes 没有 config 选项来更改大多数数据目录
- Junction 是透明的——所有程序看到的是同一个路径
- 可逆（删 Junction 恢复备份）

### 迁移流程（5 步）

```bash
# 1. 创建目标目录
mkdir -p "D:/Hermes file/skills"

# 2. 复制现有内容
cp -r "$HOME/AppData/Local/hermes/skills/"* "D:/Hermes file/skills/"

# 3. 备份原目录
mv "$HOME/AppData/Local/hermes/skills" "$HOME/AppData/Local/hermes/skills.bak"

# 4. 创建 Junction（用 PowerShell，不用 mklink）
powershell -Command "New-Item -ItemType Junction -Path 'C:\Users\dairch\AppData\Local\hermes\skills' -Target 'D:\Hermes file\skills'"

# 5. 验证
ls "$HOME/AppData/Local/hermes/skills/"  # 确认可访问
```

### mklink 的坑

```bash
# 错误 — mklink 在 git-bash 中处理含空格路径时乱码
cmd //c "mklink /J \"C:\...\" \"D:\Hermes file\skills\""
# → "文件或目录的名称语法不正确"

# 正确 — PowerShell 正确处理空格
powershell -Command "New-Item -ItemType Junction -Path '...' -Target '...'"
```

### 迁移状态（我的环境）

| 目录 | 已迁移？ | 说明 |
|------|---------|------|
| skills | ✅ | D:\Hermes file\skills\ |
| sessions | ✅ | SQLite DB |
| cache | ✅ | 模型缓存 |
| image_cache | ✅ | 图片缓存 |
| audio_cache | ✅ | TTS 缓存 |
| logs | ❌ | 被 gateway 锁，需先 `hermes gateway stop` |
| hermes-agent | ⚠️ | 35K文件，迁移后需测试 `hermes update` |
| config.yaml | ❌ | 必须留在原位 |
| .env | ❌ | 必须留在原位 |

---

## 3. Gateway 日常运维

### 基本命令

```bash
hermes gateway run       # 前台运行（调试用）
hermes gateway start     # 后台服务
hermes gateway stop      # 停止
hermes gateway status    # 状态
hermes gateway restart   # 重启
```

### Gateway 崩溃恢复

```bash
# 替换已有进程
hermes gateway run --replace

# 等 15 秒让 Telegram polling 初始化
# 验证
tail -5 ~/AppData/Local/hermes/logs/gateway.log
# 应显示: telegram connected
```

### 日志查看

```bash
# 最近错误
grep -i "failed to send\|error" ~/AppData/Local/hermes/logs/gateway.log | tail -20
```

---

## 4. Memory Provider 切换

```bash
# TUI 方式（可能失败）
hermes memory setup

# 直接配置（推荐）
hermes config set memory.provider scope-recall
hermes config set memory.provider ''   # 回 built-in

# 验证
hermes memory status
```

---

### 下一步

→ [02 · Python 环境与代理](02-python-proxy-env.md)
