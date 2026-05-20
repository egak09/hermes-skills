---
name: redundant-verification
description: "工程控制论Ch17启发 — 对不可逆/高风险操作执行前后双检+独立路径确认。触发：rm/git push/公共频道消息等。"
version: 1.0.0
category: software-development
---

# 冗余验证协议 (Redundant Verification)

> **来源：** 钱学森《工程控制论》第17章 — 可靠性与冗余
> **核心理念：** 通过冗余（独立第二路径）换取可靠性。单点确认不可信——工具返回码 ≠ 实际结果。

## 触发条件（满足任一）

| 操作类型 | 示例 |
|---------|------|
| 不可逆删除 | `rm`, `git reset --hard`, 删除文件/目录 |
| 强制推送 | `git push -f`, `git push --force` |
| 数据库写操作 | DROP TABLE, DELETE FROM, TRUNCATE |
| 发送消息到公共频道 | send_message 到非 DM 目标 |
| 影响超出当前会话 | 修改共享配置、发布到外部平台 |

## 协议步骤

### 1. 执行前确认
在执行高风险操作**之前**，打印简短确认：
```
⚠️ 高风险操作: {具体操作}
理由: {为什么需要这么做}
```

### 2. 执行操作
正常执行。

### 3. 独立路径确认
**用不同于操作的路径验证结果** — 这是冗余的核心：

| 操作 | 独立验证路径 |
|------|------------|
| write_file / patch | read_file 回读关键段落（不只信任 write 返回码） |
| git push | git ls-remote origin HEAD 确认远端 SHA |
| 删除文件 | ls / search_files 确认文件已消失 |
| HTTP POST / PUT | 独立 GET 请求确认资源存在且内容正确 |
| send_message | 不做额外验证（平台 ACK 即可，且重复发送有害） |

### 4. 对比预期 vs 实际
```
预期: {应该发生什么}
实际: {独立路径看到什么}
结论: ✅ 一致 / ❌ 不一致
```

### 5. 不一致时
立即报告 + 尽可能给出回滚/修复建议。不要沉默。

## 陷阱与误区

- ❌ 不要信任工具返回码 — write_file 返回成功 ≠ 内容写对了
- ❌ 不要对低风险操作做冗余验证 — 每次文件写入都双检 = 2x 延迟
- ❌ 验证路径必须独立于操作路径 — 同一个 API 调两次不是冗余
- ✅ send_message 是唯一豁免 — 平台 ACK 足够，重复发送会刷屏
- ✅ 文件写入只需回读关键段落 — 不用读整个文件

## 示例

用户："把这个 push 上去"

```
⚠️ 高风险操作: git push origin main
理由: 确认本地 commits 已就绪

[执行 git push]

🔍 冗余验证:
git ls-remote → HEAD SHA: abc1234
本地 HEAD SHA:    abc1234
✅ 一致 — 远端已同步
```
