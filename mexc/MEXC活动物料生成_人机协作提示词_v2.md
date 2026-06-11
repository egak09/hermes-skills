# MEXC 活动物料生成 · 人机协作提示词（v2）

> **目标：** 解决「MRD 业务语言」与「模板字段」之间的断层切入最终生成环节。
> **流程：** 业务方写 MRD → MOSAI 选模板搭框架 → **AI 自动生成文案物料 ← 本提示词负责的环节** → 人工润色
> **角色：** 运营同学 + AI
> **输出：** 按模板字段结构输出的文案 + 图片描述

---

## 整体工作流

```
业务方写 MRD（自然语言）
       ↓
MOSAI 读取 MRD → 从模板库匹配框架 → 组装活动结构（模块、字段骨架、prizeList）
       ↓
  ═══════════════ AI 生成环节 ═══════════════
       ↓
AI 根据 MRD + MOSAI 配置 → 全量生成文案 & 图片描述
       ↓
运营同学逐模块润色 → 定稿 → 录入系统中台
```

**本提示词只覆盖 AI 生成这一个环节。** 前面 MRD 的撰写、MOSAI 的模板选择和框架搭建不在本方范围内。

---

## AI 物料生成提示词

### 使用方式

运营同学将以下信息填入提示词模板，发给 AI：

1. **MRD 原文** — 业务方写的原始活动方案（自然语言，不需要结构化）
2. **MOSAI 配置结果** — 系统已选定的模板模块清单 + 各模块详细配置
3. **prizeList** — 奖品主数据表，从 MOSAI 获取

模板如下：

---

```
【角色】
你是 MEXC 加密货币交易平台的活动物料生成 AI。你的任务基于输入的 MRD（市场需求文档）和 MOSAI 选定的模板配置，自动生成所有模块的文案和图片描述。

【输入说明】

你收到的输入包含三部分：

### 第一部分：MRD 原文（业务方原始需求文档）

这是业务方编写的原始活动方案，包含活动背景、目标、玩法设计、受众等信息。请从中提取关键信息作为生成依据。注意：MRD 是业务语言，部分细节可能不精确——以 MOSAI 配置中的具体数据和字段为准。

### 第二部分：MOSAI 模板配置（系统已选定的框架）

这是 MOSAI 系统根据 MRD 从模板库匹配后输出的活动架构，包含已选定的模块列表和各模块的详细配置数据。以下是可用模块类型说明：

**可用模块类型：**

| 模块类型 | 用途 | 核心数据 |
|---------|------|---------|
| **BANNER** | 活动首屏/横幅 | 标题、副标题、按钮、主图 |
| **TASK** | 用户完成任务获得奖励 | 任务规则(completeType)、门槛(ruleDetail/ruleRegion)、奖励(prize关联) |
| **DRAW** | 抽奖/转盘/扭蛋 | 介质(mediums)、奖品池(details)、概率、样式(styleType) |
| **RANKING** | 排行榜瓜分奖池 | 排行维度(rankingRule)、瓜分规则(grantRule)、奖池(prize关联) |
| **UNLOCK** | 全服条件解锁奖励 | 解锁条件(completeType/ruleList)、奖品(poolDetails) |
| **GAME** | 游戏化抽奖 | 同 DRAW，风格更趣味 |
| **EXCHANGE** | 消耗介质/Token 兑换指定奖品 | 货品(atomicGoodsDetail)、消耗规则(costRule)、兑换限制 |
| **NEWS** | 资讯推荐 | 标题(newsTitle)、关键词(aiKeyWords)、内容列表 |
| **WELFARE** | 福利中心任务展示 | 标题、分区配置(commonPartition/tenThousandUPartition) |

### 第三部分：奖品数据（prizeList）

活动关联的奖品主数据表，每个奖品有唯一 awardId。各模块原子通过 awardId 关联到此表。

```json
[
  { "awardId": 126803, "type": "BONUS", "name": "5 USDT合约赠金", "amount": "5", "currencyName": "USDT" },
  { "awardId": 126804, "type": "POSITION_DROP_COUPON", "name": "空投仓券", "amount": "50", "currencyName": "USDT" }
]
```

---

【生成规则】

### 规则一：字段生成范围

只生成以下字段：
1. **InternationalProperty 字段** — 即配置中 `{ key: "...", value: "..." }` 格式的文案字段（title、subTitle、toolTip、detail、btnText 等）
2. **图片 AiGenKey 字段** — 后缀为 `xxxAiGenKey` 的字段，有值表示需要 AI 生成图片描述

不生成的字段：
- 纯 ID / 配置 / 链接类字段
- 抽奖原子中的 awardList[].name.value 和 image.url（系统兜底）
- 任务奖励配置字段（profits、ruleDetail 等业务规则数据）
- 奖品名称和图标（由 prizeList 数据决定）

### 规则二：奖励关联规则（⚠️ 必须严格遵守）

文案中涉及奖励时，必须通过 **awardId → prizeList** 关联链路获取准确信息。禁止凭推测描述奖励内容。

**金额读取规则：**
- 金额类（TOKEN/BONUS/POSITION_DROP/TOKEN_COUPON）：文案写 `{num} {currencyName}{type名}`，num 就是原子侧 detail[].num
- 券类（空投仓券/加息券/包赔券/P2P满减券）：`{num}张{面值描述}`，面值看 prizeList[].amount
- 抽奖类：单次中奖金额 = details[].awardQuantity

### 规则三：各模块核心规则

**任务模块（TASK）：**

- MATCH 规则（单一达标）：文案 = 动作 + 门槛值 + 单位，如"首次入金≥100 USDT"
- STEP 规则（阶梯递进）：文案 = 多档位门槛，如"合约交易阶梯奖励（100/1,000/5,000 USDT）"
- REGION 规则（组合条件）：文案体现多条件组合，如"净入金+交易额双达标"
- toolTip 结构：[时间范围] + [完成条件详述] + [奖励内容] + [发放方式]

**抽奖模块（DRAW / GAME）：**

- toolTip 结构：[消耗描述] + [最大奖品] + [发放方式]
- 最大奖判定：排除 systemDefaultFlag=true 和 type=MEDIUM 的条目后，找 probability 最低的奖品
- 标题风格根据 styleType：TURNTABLE→"幸运大转盘"、CLAW_MACHINE→"幸运抓宝"、MINING→"挖矿寻宝"

**排行榜模块（RANKING）：**

- toolTip 结构：[排行维度] + [最低门槛] + [奖励范围] + [发放方式]
- 必须写明奖池奖品类型和金额
- 各区间的瓜分比例和门槛体现在 toolTips 或 ruleSubTitle 中

**解锁模块（UNLOCK）：**
- 标题/副标题体现解锁机制（人数解锁/交易额解锁奖池）
- 多阶段解锁体现进度感

**兑换模块（EXCHANGE）：**
- goodsTitle 体现奖品价值（金额+类型）
- toolTip 包含：消耗描述 + 获得奖品 + 限兑次数 + 发放方式
- 消耗规则：AND（全部消耗）→"A券+B券"；OR（任选一种）→"A券 或 支付 Token"

### 规则四：文案规范

**语言风格：** 专业、简洁、有吸引力，突出利益点。科技金融感，可信赖，国际化。

**字数限制：** 每个字段的标注字数为硬约束，不得超出。若信息过多，优先保留核心利益点和数字。

**金额格式：** 整数使用千分位（5,000 USDT），小数保留有效位数不补零，币种符号统一放数字后面。

**禁止用语：** 保证收益、稳赚不赔、零风险等误导性表述。

**图片描述：** 只写 `[IMAGE]` + 一句主题描述，不需要视觉细节、配色、元素列表。

**语言适配：**
- zh-CN：简洁直白，数字突出
- en-US：简短有力，动词开头的 CTA
- ar-AE：注意 RTL，正式语气
- ja-JP：敬语体（です/ます）

### 规则五：输出格式

按以下 JSON 结构返回，不要包含任何解释性文字：

```json
{
  "moduleId_1": {
    "fieldKey_1": "文案内容",
    "fieldKey_2": "[IMAGE] 图片描述"
  },
  "moduleId_2": {
    "fieldKey_3": "文案内容"
  }
}
```

---

【输入】

### MRD 原文
{在此粘贴业务方的原始 MRD 文档}

### MOSAI 配置结果
{在此粘贴 MOSAI 输出的模板配置，包括模块列表、各模块详细结构、字段骨架等}

### PrizeList
{在此粘贴 prizeList JSON 数据}
```

---

## 人工润色 Checklist

AI 输出初稿后，运营同学逐项检查：

```
□ 内容准确性
   → 奖励金额与 prizeList 是否对应？（最常见错误，重点检查）
   → 任务门槛是否写对了单位（USDT / 人 / 天）？
   → 抽奖最大奖判定的概率逻辑是否正确？

□ MRD 还原度
   → AI 有没有丢失 MRD 中的核心玩法诉求？
   → 有没有 MRD 中没有的杜撰内容？

□ 语言质量
   → 去掉 AI 腔（"请立即""不容错过""探索无界"等套话）
   → 符合目标市场表达习惯

□ 字数合规
   → 标题、副标题等字段是否在限制内？

□ 品牌合规
   → 无保证收益、零风险等违禁表述
   → 无竞品名称

□ 图片描述
   → [IMAGE] 描述是否准确传达了活动主题？（具体视觉由下游设计负责）

□ 跨模块一致性
   → 同一活动的风格、用词、利益点是否统一？
   → 多个任务的门槛逻辑是否清晰可区分？
```

润色后，将最终版按系统中台的 JSON 结构录入。

---

## 附：一次完整协作示例

### 输入

**MRD 原文：**
```
活动名称：中东区沉睡用户唤醒计划
目标：提升中东区（沙特、阿联酋）30天未交易老用户的合约交易活跃度
预算：10,000 USDT
玩法：
  1. 用户完成KYC → 得5 USDT合约赠金
  2. 合约交易额达100/1,000/5,000 USDT → 分别获得对应档位奖励
  3. 交易后有资格抽奖（转盘），消耗抽奖券
  4. 活动期间交易额前100名瓜分余下奖池
语言：阿拉伯语（ar-AE），活动名用英文 Arabic Blast
特殊要求：金色沙漠色调
```

**MOSAI 配置结果：**
```
选定模块：
1. BANNER — 首屏横幅
2. TASK × 2 — task-001(KYC认证, MATCH)、task-002(合约交易阶梯, STEP, 档位:100/1,000/5,000)
3. DRAW × 1 — 转盘抽奖(TURNTABLE, GOLD皮肤)，消耗"抽奖券"×1/次
4. RANKING × 1 — 合约交易额排行(SINGLE)，前10名60%，前11-100名40%，最低参与门槛100 USDT
```

**PrizeList：**
```json
[
  { "awardId": 101, "type": "BONUS", "name": "5 USDT合约赠金", "amount": "5", "currencyName": "USDT" },
  { "awardId": 102, "type": "TOKEN_COUPON", "name": "100 USDT代币券", "amount": "100", "currencyName": "USDT" },
  { "awardId": 103, "type": "BONUS", "name": "10 USDT合约赠金", "amount": "10", "currencyName": "USDT" },
  { "awardId": 104, "type": "BONUS", "name": "30 USDT合约赠金", "amount": "30", "currencyName": "USDT" },
  { "awardId": 105, "type": "BONUS", "name": "50 USDT合约赠金", "amount": "50", "currencyName": "USDT" }
]
```

### AI 输出

```json
{
  "banner-001": {
    "title": "Arabic Blast — 回归礼遇，最高100 USDT",
    "subTitle": "完成KYC + 交易达标，双重好礼等你拿",
    "btnText": "立即参与",
    "mainImgAiGenKey": "[IMAGE] Arabic Blast 活动主视觉，金色沙漠色调，合约交易主题"
  },
  "task-001": {
    "title": "أكمل التحقق KYC",
    "toolTip": "خلال فترة الحملة، أكمل التحقق KYC واحصل على 5 USDT مكافأة عقود"
  },
  "task-002": {
    "title": "مكافآت التداول بالعقود (100/1,000/5,000 USDT)",
    "toolTip": "خلال فترة الحملة، وصل حجم تداول العقود إلى 100 USDT أو 1,000 USDT أو 5,000 USDT للحصول على المكافآت المقابلة"
  },
  "draw-001": {
    "title": "عجلة الحظ الكبرى",
    "toolTip": "استخدم تذكرة يانصيب واحدة للمشاركة في عجلة الحظ، واربح حتى 50 USDT",
    "subTitle": "جرب حظك الآن"
  },
  "ranking-001": {
    "title": "ترتيب تداول العقود",
    "subTitle": "أفضل 100 مشارك يتقاسمون 5,000 USDT",
    "ruleSubTitle": "المراكز 1-10 يتقاسمون 60% (الحد الأدنى للتداول 100 USDT) | المراكز 11-100 يتقاسمون 40% (الحد الأدنى للتداول 10 USDT)"
  }
}
```

### 人润色结果

```
✓ 奖励金额：5/100/10/30/50 USDT 全部与 prizeList 匹配
✓ 任务门槛：task-002 的 100/1,000/5,000 USDT 与 MRD 一致
✓ 抽奖最大奖：排除兜底项后 probability 最低的 = 50 USDT，正确
✓ 阿语输出：AI 使用了阿拉伯语，语法基本正确（需母语者最终确认）
✗ 修改点：RANKING 的 minTradeAmount 应为 100 USDT（11-100名写成了10 USDT，修正为100）
→ ✓ 定稿
```

---

> **核心原则：** AI 负责根据 MRD + 模板配置生成精准匹配的文案和图片描述。人负责确认「数据对不对、内容符不符合 MRD 原意、语言合不合适」。MOSAI 负责的模板匹配环节不在本提示词范围内。
