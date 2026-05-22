# C盘瘦身实战记录

> 2026-05-22 执行，回收约 1 GB

---

## 扫描结果

磁盘: 129.6/145.4 GB (89.1%)，空闲 15.8 GB

---

## Phase 1: Windows 系统垃圾（已完成）

| 清理项 | 预估大小 | 结果 |
|--------|---------|------|
| User Temp | 1.8 GB | ✅ |
| System Temp | 397 MB | ✅ |
| Chrome 缓存 | 228 MB | ✅ |
| pip 缓存 | 178 MB | ✅ |
| Windows Logs (>7d) | 173 MB | ✅ |
| 回收站 | 63 MB | ✅ |
| Edge 缓存 | 11 MB | ✅ |
| 缩略图缓存 | 10 MB | ✅ |

**回收**: 已用 129.6 → 128.7 GB，空闲 15.8 → 16.7 GB

---

## Phase 2: Hermes 目录 Junction 迁移（待执行）

| 目录 | 文件数 | 风险 |
|------|--------|------|
| `logs/` | 6 | 需停 Gateway 30 秒 |
| `plugins/` | 116 | 安全 |
| `scope-recall/` | 31 | 安全 |
| `hermes-agent/` | 39,944 | 需测试 update |

---

## 已迁移（之前完成）

skills / sessions / cache / image_cache / audio_cache → D:\Hermes file\
