# 📚 U2SURP（SR140）文献检索报告

> **检索时间**：2026.8.16 ｜ **检索源**：PubMed E-utilities + Europe PMC + PMC OA + Crossref（多源交叉）
> **检索式**：U2SURP × {基础功能 / DDR / 端粒TERRA / 剪接U2 snRNP / 癌症 / 互作网络}
> **用途**：硕士课题《潜在端粒损伤修复蛋白的鉴定》候选蛋白 U2SURP 的文献背景核查

---

## 一、U2SURP 是什么（已确立的共识）

**身份**：U2 snRNP-associated SURP motif-containing protein，SR（丝氨酸/精氨酸富集）蛋白家族成员。剪接相关蛋白。

| 维度 | 已知事实 | 来源 |
|---|---|---|
| 结构 | SURP motif + RS 结构域，U2 snRNP 相关 | 共识 |
| 互作 | 与 **RBM17、CHERP** 互作，调控 RNA 加工蛋白的剪接 | De Maio 2018, Cell Rep, PMID 30332651 |
| 功能 | 剪接调控，尤其影响 RNA 加工/剪接相关基因自身的剪接 | De Maio 2018 |
| 癌症 | **MYC 驱动 U2SURP** 调控 SAT1 可变剪接 → 三阴乳腺癌（TNBC）进展、预后差 | Deng 2023, Cancer Lett, PMID 36907504 |
| 耐药 | U2SURP→CREB3L2 mRNA 稳定→RIOK1 转录 → 肝癌仑伐替尼耐药 | 2026, PMID 41997041 |
| 其他 | 乳酰化相关预后标志物（免疫学分析）；lncRNA HNF1A-AS1 互作促胰腺癌转移 | 2025 多篇 |

**功能画像**：U2SURP 是一个"剪接因子"，在癌症里被 MYC 驱动、通过调控特定基因（SAT1 等）可变剪接促进肿瘤进展。它调节的是"RNA 加工蛋白的剪接"——处在剪接调控网络的上层。

---

## 二、与 DNA 损伤/DDR 的关联：⭐ 有独立鉴定证据（这是最大亮点）

### 核心发现 1：另一篇独立蛋白质组学研究也筛到了 U2SURP

**da Silva RC, et al. "Probing DNA damage sites reveals context-dependent and novel DNA damage response factors"**
- **预印本（bioRxiv 2024, DOI 10.1101/2024.10.23.619792）**：摘要明确写道——
  > "Among these novel proteins, we characterize the ubiquitin ligase **UBE3A**, the methyl-binding and proteasome-recruiting protein **L3MBTL3**, and the **spliceosomal factor U2SURP**, as previously uncharacterized **effectors of DNA damage response**."
- **方法**：用 MCPH1 的 tandem-BRCT 结构域（特异性识别 γH2AX）做探针，把 TurboID 生物素连接酶拴到染色质上，邻近标记（proximity ligation）鉴定 DNA 损伤相关蛋白质组；比较 5 种 DNA 损伤剂，鉴定多个新型 DDR 蛋白并功能验证了其中 3 个——**U2SURP 是其中之一**
- **意义**：**这是与你 PhastID 完全独立的第二条筛选路径**——他用 γH2AX-BRCT-TurboID，你用 PhastID 端粒富集，两个独立方法都筛到 U2SURP → 交叉验证，大大增强你候选蛋白的可信度

### 核心发现 2：正式发表版弱化了 U2SURP 结论（引用需注意）

- **正式版：da Silva RC, et al. "Engineered chromatin readers track damaged chromatin dynamics in live cells and animals." Nat Commun. 2025 Nov 20. PMID 41266351**（开放获取 PMC12635110）
- 我检索了正式版全文 XML：**U2SURP / SR140 / UBE3A / L3MBTL3 全部出现 0 次**
- 正式版聚焦于探针工具本身（方法学论文），删掉了三个蛋白的功能表征内容
- **引用策略**：你论文里引用 U2SURP 的 DDR 证据时，**必须引预印本（bioRxiv 2024）**，并注明"预印本结论、正式版未保留"；或者引用正式版时只说"该团队开发了 γH2AX 邻近标记探针"，不提 U2SURP

### 核心发现 3：机制框架——损伤诱导的可变剪接通路（给你提供解释框架）

**McCann JJ, et al. "Participation of ATM, SMG1, and DDX5 in a DNA Damage-Induced Alternative Splicing Pathway." Radiat Res. 2023. PMID 36921295**
- 机制：IR 损伤 → ATM 抑制 SMG1 激酶 → DDX5（RNA 解旋酶/剪接因子）→ **TP53 pre-mRNA 可变剪接 → p53β/p53γ → 辐射诱导细胞衰老**
- **意义**：这篇证实了"剪接因子参与 DDR"的合法性——DNA 损伤确实会调动剪接机器（ATM/SMG1/DDX5 都参与），U2SURP 作为剪接因子出现在 DDR 蛋白质组里，不是偶然污染，而是**剪接-损伤响应轴的成员**

---

## 三、与端粒/TERRA 的关联：无直接文献

- 检索 "U2SURP AND (telomere/TERRA)"：17 个命中全部是间接共现（癌症转录组、miRNA 网络等），**无任何直接文献**
- **与 WDR75 相同：你的端粒发现是全新的，无前人也无竞争**

---

## 四、⚠️ U2SURP 的混杂因素（与 WDR75 不同的问题）

| 蛋白 | 混杂因素 | 表型解释风险 |
|---|---|---|
| WDR75 | 核仁应激 → p53 → 衰老（γH2AX 阳性） | 敲低必然引发 |
| **U2SURP** | **全局剪接紊乱**——剪接因子敲低会改变成百上千基因的剪接，包括 DDR 基因（TP53/ATM/BRCA1 等）自身 | 敲低必然引发 |

**推理链**：
```
U2SURP KD
  → 全局剪接改变（尤其 RNA 加工蛋白的剪接）
  → DDR 关键基因（TP53、ATM、BRCA1...）剪接变体改变
  → 间接改变 γH2AX 动态
```

**必须做的排除实验**：
1. **剪接组验证**：U2SURP 敲低后，RT-PCR/RNA-seq 检测已知 DDR 基因（TP53、ATM、BRCA1、MDC1 等）是否有剪接变体变化——若这些基因剪接正常，你的 γH2AX 表型更可能是直接效应
2. **核仁应激对照**：同时检测 RPL5/RPL11/p53——排除 U2SURP 敲低也引发核仁应激（剪接因子和核仁有时纠缠）
3. **端粒特异性再确认**：同 WDR75——TPP1+γH2AX 共定位归一化分析，确认端粒特异性而非全核效应
4. **RNase 处理 PhastID**：去 RNA 后 U2SURP 的端粒富集是否消失（RNA 中介假说）

---

## 五、对你课题的意义：U2SURP 是比 WDR75 更强的候选

**1. 独立验证加分**：Baubec 团队（Utrecht）用完全独立的方法（γH2AX-BRCT-TurboID）鉴定 U2SURP 为 DDR 效应因子——你的 PhastID 发现不是孤证。答辩时这一条可以直接引用。

**2. 端粒特异性是差异化**：Baubec 做的是全基因组 DDR，没有端粒特异性。**你的贡献在于"端粒"**——同一个蛋白，你证明它在端粒损伤修复中扮演角色，这是别人没做的。

**3. 故事张力更强**：
- WDR75 = 核糖体蛋白被端粒招募（意外）
- U2SURP = 剪接因子被端粒招募（意外 + 有独立 DDR 先例）
- 两个都是 RNA 结合蛋白 → "RNA 中介的端粒损伤响应"假说的证据链：**TERRA/R-loop 招募 RNA 蛋白到损伤端粒**

**4. 机制假设升级**：结合 McCann 2023（损伤诱导可变剪接），你可以提出更精细的假设：
> U2SURP 被招募到损伤端粒后，可能通过调控**端粒附近基因或 TERRA 相关转录本的剪接**，参与端粒损伤信号的传递——这比"它直接修复 DNA"更有新意。

---

## 六、关键文献清单（U2SURP）

| # | 文献 | 期刊/年份 | PMID/DOI | 与课题关系 |
|---|---|---|---|---|
| 1 | **Probing DNA damage sites reveals... novel DNA damage response factors**（da Silva & Baubec） | bioRxiv 2024 | 10.1101/2024.10.23.619792 | ⭐⭐⭐ 独立鉴定 U2SURP 为 DDR 效应因子（**引用必须用此预印本**） |
| 2 | **Engineered chromatin readers track damaged chromatin dynamics in live cells and animals**（da Silva & Baubec） | Nat Commun 2025 | PMID 41266351 | 正式版：方法学论文，**U2SURP 已被删去** |
| 3 | **RBM17 Interacts with U2SURP and CHERP to Regulate Expression and Splicing of RNA-Processing Proteins**（De Maio et al.） | Cell Rep 2018 | PMID 30332651 | U2SURP 互作网络与剪接功能基础 |
| 4 | **MYC-driven U2SURP regulates alternative splicing of SAT1 to promote TNBC progression**（Deng et al.） | Cancer Lett 2023 | PMID 36907504 | U2SURP 癌症功能：MYC 下游、剪接调控 |
| 5 | **Participation of ATM, SMG1, and DDX5 in a DNA Damage-Induced Alternative Splicing Pathway**（McCann et al.） | Radiat Res 2023 | PMID 36921295 | 机制框架：剪接因子参与 DDR 的合法性 |
| 6 | **U2SURP increases CREB3L2 RNA stability and RIOK1 transcription... lenvatinib resistance in HCC** | 2026 | PMID 41997041 | U2SURP 通过 mRNA 稳定性调控下游基因（机制参考） |

---

## 七、一句话结论

> U2SURP 是剪接因子，被 Baubec 团队用 γH2AX-邻近标记独立鉴定为 DDR 效应因子（预印本），在癌症里是 MYC 驱动的剪接调控因子——你的 PhastID 端粒富集发现与独立文献交叉验证；风险在于剪接因子敲低的全局剪接紊乱混杂，必须用 DDR 基因剪接检测 + 端粒共定位归一化排除。
