# 07 · 写作工坊

> Paradigme 的文学分析与推文创作空间

---

## 目录结构

```
07-writing-workshop/
├── README.md           ← 你在这里
├── literature/         ← 文学分析笔记（俄国文学、课程论文、书评等）
└── tweet-drafts/       ← 推文草稿、Threads、发推策略
```

## 文学（literature/）

存放你的俄国史论文、文学课程笔记、以及其他文学作品的分析。
- 《从告青年到互助论》— 克鲁泡特金读书报告
- 《卡拉马佐夫兄弟》— 陀思妥耶夫斯基课程论文
- 俄国史复习要点— 涵盖十二月党人、民粹派、斯拉夫派/西方派、恰达耶夫等

## 推文创作（tweet-drafts/）

由 Hermes Agent 基于 `paradigme-writing-style` skill 生成的推文草稿和发推策略。
- 加密简报 → 提炼可发推内容
- 叙事分析 → 推文 Threads
- 市场洞察 → 短推文

## 产出流程

```
数据采集（BlockBeats/Odaily）
    ↓
AI 分析 + 风格化写作（paradigme-writing-style skill）
    ↓
草稿推文 → 保存到 tweet-drafts/
    ↓
Paradigme 手动润色
    ↓
发布到 X (@sky_dai7334)
```

## 风格指南

写作风格请参考 `content/paradigme-writing-style/SKILL.md`
