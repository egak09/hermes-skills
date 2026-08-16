# 📚 WDR75 文献检索报告

> **检索时间**：2026.8.16 ｜ **检索源**：PubMed E-utilities + Europe PMC（双源）
> **检索式**：WDR75 × {基础功能 / DDR / 端粒 / 核仁应激 / rRNA加工 / 癌症p53 / 基因组稳定性}
> **用途**：硕士课题《潜在端粒损伤修复蛋白的鉴定》候选蛋白 WDR75 的文献背景核查

---

## 一、WDR75 是什么（已确立的共识）

**身份**：SSU processome（小亚基加工体，71蛋白复合物）核心成员，人类核糖体生物发生必需因子。

| 维度 | 已知事实 | 来源 |
|---|---|---|
| 复合物 | UTP-B 复合物成员，参与 pre-rRNA 5'ETS 加工 | 多篇共识 |
| 定位 | **核仁蛋白**（内源），核仁应激时重定位到 **nucleolar caps** | Moudry 2022, PMID 34611297 |
| 功能 | 结合 rRNA 外部转录间隔区（ETS）保守基序，帮助形成 SSU；**维持 RPA194（RNA Pol I 大亚基）水平，为 pre-rRNA 转录所必需** | Lee 2025 (PLoS ONE)；Moudry 2022 |
| 进化 | 70个哺乳动物序列比较：~25% 位点受纯化选择（净化选择），β-折叠位点选择压力比卷曲强 5x，无正选择证据——**功能重要且保守** | Lee 2025, PMID 39932919 |
| 疾病 | WDR75 双等位变异 → B 细胞免疫缺陷 + rRNA 加工缺陷（人类病例，2026） | Moreno-Corona 2026, PMID 42099922 |

**p53 连接（最关键）**：siRNA 筛选 175 个核糖体生物发生因子中，**WDR75 敲低 → p53 累积**（U2OS 验证多模型）。机制：WDR75 缺失 → pre-rRNA 转录受损 → 激活 **RPL5/RPL11 依赖的核仁应激检查点** → p53 稳定 → **增殖受损 + 细胞衰老**。
（Moudry P, et al. Cell Death Differ. 2022;29(3):687-696. PMID 34611297）

---

## 二、与 DNA 损伤/DDR 的直接关联：**几乎没有直接文献**

检索 "WDR75 AND (DNA damage/DDR/telomere)" 的发现：

- **WDR75 + 端粒**：无任何直接文献。17 个命中全部是间接共现（癌症转录组、QTL 定位等）
- **WDR75 + DDR**：无直接报道。最接近的是间接框架文献（如 p53 在复制与核糖体应激交叉路口的综述，Lindström 2022, PMID 35444234）
- **同复合物邻居**：UTP11（同 UTP-B）缺陷 → 核仁应激 + 铁死亡 → 抑制癌症（Redox Biol 2023, PMID 37087976）；BRIX1 靶向 → 核仁应激抑癌（Adv Sci 2024）——**UTP-B 成员敲低的标准后果就是核仁应激 → p53 通路**

---

## 三、⚠️ 对课题最重要的发现：一个必须排除的混杂因素

**WDR75 敲低后的 γH2AX 升高，可能不是"端粒修复缺陷"，而是核仁应激的间接后果。**

推理链：
```
WDR75 KD
  → pre-rRNA 转录受损（RPA194 下降）
  → 核仁应激
  → RPL5/RPL11 → p53 稳定
  → 细胞衰老（senescence）
  → 衰老相关 DNA 损伤（SASP/SA-DDR）→ γH2AX 升高
  → 也可能影响细胞周期 → 间接改变 γH2AX 基线
```

**这与"WDR75 直接参与端粒 DSB 修复"是竞争性假说**，答辩时必被问到。Moudry 2022 已经证明 WDR75 KD 会导致衰老——衰老细胞本身就是 γH2AX 阳性的（senescence-associated DNA damage foci），这是文献金标准结论，你的表型需要在这个背景下重新解读。

### 必须做的排除实验（按优先级）

1. **p53/p21 检测**：WDR75 敲低细胞 WB 检测 p53 总量 + p21（若 p21 大幅上调 → 核仁应激通路激活坐实）
2. **衰老标志**：SA-β-gal 染色，或 4/8h 时间点的 γH2AX 基线（未照射组）——若未照射的 KD 细胞 γH2AX 基线就高，表型可能主要来自衰老
3. **端粒特异性再确认**：你已有的 TPP1+γH2AX 共定位是**最有价值的区分工具**——如果受损端粒比例在 KD 后特异性升高（扣除全核 γH2AX 升高），才能把故事锚定到端粒；建议补一个"端粒信号占比 vs 全核信号"的归一化分析
4. **时间窗判读**：IR 后 2-8h 的 γH2AX 清除延迟指向"修复缺陷"；而 24h+ 或未照射基线升高指向"衰老/核仁应激"——你现有数据（2-8h）其实偏向修复缺陷解释，这反而是好消息，但要确认未照射对照组基线
5. **rescue 关键对照**：回补野生型 WDR75 应同时挽救 rRNA 加工和 γH2AX 表型；若能找到"维持 rRNA 加工但不影响修复"的突变体（分离表型），就能彻底区分两条通路

---

## 四、核仁帽（nucleolar caps）——一个可能反转故事的联系

Moudry 2022 发现 WDR75 在化学诱导核仁应激时**重定位到 nucleolar caps**。核仁帽是 DNA 损伤（尤其 rDNA 损伤）时核仁蛋白的典型重排结构，也出现在端粒损伤相关研究中。

这条线索的两种解读：

- **消极解读**：WDR75 在 IR 后"富集到端粒"可能只是核仁应激下蛋白从核仁逃逸、非特异贴附到染色质的旁观效应
- **积极解读**：nucleolar caps 的形成本身是 DDR 的一部分，WDR75 作为 RNA 结合蛋白随 RNA:DNA 杂合体（R-loop）移动，可能确实参与损伤位点的 RNA 代谢——**这正好接上你的 TERRA/R-loop 假说**

**判别实验**：PhastID 富集实验加 RNase 组（去 RNA 后富集是否消失）；或对 IR 后细胞的 WDR75 做 RNA-FISH（TERRA）共定位。

---

## 五、对课题叙事的意义

1. **选题正确性**：WDR75 是"非经典 DDR 蛋白被端粒损伤招募"的绝佳案例——它的已知功能（核仁/rRNA/RNA结合）与端粒修复零重叠，PhastID 筛到它本身就是 RNA 中介假说的证据
2. **故事升级路径**：`核仁应激 → p53 → 衰老` 是"系统完整性"的另一面——细胞用衰老牺牲单细胞保整体；而 WDR75 在端粒的潜在角色是"修复"——**同一个蛋白可能在两条完整性保卫战线上都有戏**
3. **答辩防线**：先讲清楚排除实验（第三节），再讲功能实验，叙事才站得住

---

## 六、关键文献清单（按重要性）

| # | 文献 | 期刊/年份 | PMID/DOI | 与课题关系 |
|---|---|---|---|---|
| 1 | **RNA-interference screen for p53 regulators unveils a role of WDR75 in ribosome biogenesis** (Moudry et al.) | Cell Death Differ 2022 | PMID 34611297 | ⭐ 最重要：KD→p53→衰老机制 + nucleolar caps 重定位 |
| 2 | **WDR75: An essential protein for ribosome assembly undergoing purifying selection** (Lee & Whittall) | PLoS ONE 2025 | PMID 39932919 | 结构/进化/保守性背景 |
| 3 | **Ribosomal RNA processing impairments in a B cell immunodeficient patient with WDR75 variants** | J Hum Immun 2026 | PMID 42099922 | 人类疾病表型 |
| 4 | **p53 at the crossroad of DNA replication and ribosome biogenesis stress pathways** (Lindström et al.) | Cell Death Differ 2022 | PMID 35444234 | 综述：核糖体应激×复制压力×p53 框架 |
| 5 | **UTP11 deficiency suppresses cancer via nucleolar stress and ferroptosis** | Redox Biol 2023 | PMID 37087976 | 同 UTP-B 家族成员的功能先例 |
| 6 | **Targeting BRIX1 via engineered exosomes induces nucleolar stress** | Adv Sci 2024 | DOI 10.1002/advs.202407370 | 核仁应激抑癌的转化应用 |

---

## 七、一句话结论

> WDR75 是核糖体生物发生必需蛋白，敲低必然引发核仁应激→p53→衰老；它在 IR 后富集到端粒的新发现，**必须先排除"核仁应激旁观效应"才能确认为端粒修复因子**——而 RNase 实验 + 端粒共定位归一化 + rescue 分离表型，就是排除它的三把钥匙。
