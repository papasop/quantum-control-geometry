# REVISION LOG — v1.2「文字与证明对象对齐修订版」

- 论文：Exact-Root Certification of Finite-Error Ordering in Quantum Control
- 修订基线 commit：`ca888e7e5585668910ee5c6379038057c5e36bfc`（v1.1 release-metadata commit）
- 输出：`exact_root_v1_2_freeze_candidate.pdf`（25 页，第二轮定点修复后）、`exact_root_v1_2_source.zip`
- 本轮全部为文字、定义、指路、引用或排版修复。**未修改任何正式证书、protocol、
  report、JSON、numerical gate、interval endpoint 或 theorem-bearing hash；未重跑
  Arb/Krawczyk；主定理范围未扩大。**
- 状态标记：fixed / clarified / documented residual / not applicable。
  每项附：修改位置、修改前后语义、是否改变数值、是否需要重跑 Arb。

---

## BR 项（构建审查发现）

### BR-01 — Theorem 1 被读成 16+8 原始坐标子集切分 — **fixed**
- 位置：`sec_mid.tex` §6.1（Eq. (24) `eq:affine`）、Theorem 1 陈述与证明；`sec_front.tex` §3。
- 前：措辞暗示把 24 个相位坐标拆成固定 16 个横截坐标 + 8 个保留 fibre 坐标。
- 后：明确写出路径相关仿射横截参数化 γ=γ̂_k+N_k x，x∈[−3×10⁻¹²,3×10⁻¹²]¹⁶，
  N_k∈R²⁴ˣ¹⁶ 为该路径冻结正交横截基；并显式声明 "We do *not* split the 24 original
  phase coordinates into a fixed subset of 16 transverse coordinates and 8 retained
  fibre coordinates"；存在/唯一性仅限声明盒内。
- 数值改变：否。重跑 Arb：否。

### BR-02 — chart 方程与不变量结论之间缺桥接 — **fixed**
- 位置：`sec_front.tex` §3.2，新增 Lemma 1（`lem:chart`，Chart validity and
  projective matching）及短证明。
- 前：Eq. (12) 的 F=0 与"projective output + complete first projective response
  matching"之间无形式桥接。
- 后：(i) w(γ)=w_ref ⟺ [ψ(γ)]=[ψ_ref]（chart 单射性）；(ii) 同 chart 下一阶
  projective derivatives 相等 ⟺ 相位对齐后 horizontal first response 相等（商法则
  相位不变性）；结论仅限声明的 projective response，不扩展到完整 Hilbert-space
  矢量、全局相位或未声明高阶响应。无新数值假设。
- 数值改变：否。重跑 Arb：否。

### BR-03 — "constraint residual ≈1e-11" 混淆未预条件残差与 Krawczyk 像 — **fixed**
- 位置：`sec_mid.tex` §6.1 Remark 2（`rem:residual`）及 Theorem 1 证明。
- 前：把优化器层面的未预条件 ‖F‖≈10⁻¹¹ 与盒半径并列，易被当作 Krawczyk 判据。
- 后：严格区分——严格包含由完整区间像 K(X)=−CF(x₀)+(I−C[DF(X)])X 决定；‖F‖≈10⁻¹¹
  仅为近似候选点的未预条件优化诊断；冻结证书未列出任何标量预条件中心残差，故正文
  不再给出该数值。最坏盒归一化利用率以方向安全上界形式引用：
  max_k ‖K_k(X)‖∞/3×10⁻¹² < 0.866 < 1（计算最大值 0.8653915…，0.866 为其向上舍入，
  方向安全地高于认证最坏利用率；不使用向下截断的 "=0.865"）。
- 数值改变：否（利用率从冻结证书读取，未新算）。重跑 Arb：否。

### BR-05 — Theorem 2 缺完整根盒量词 — **fixed**
- 位置：`sec_mid.tex` §6.2 Theorem 2 证明。
- 前：B_k 与根盒关系未显式写出。
- 后：显式写出 B_k⊇{ℰ̄(γ̂_k+N_k x): x∈[−3×10⁻¹²,3×10⁻¹²]¹⁶}，x*_k∈X 故 exact-root
  performance ∈ B_k。
- 数值改变：否。重跑 Arb：否。

### BR-06 — B_k 看似只在盒心/近似根求值 — **clarified**
- 位置：同 BR-05。
- 后：明确 B_k 是整个声明横截盒上的 outward-rounded 区间包围，"evaluated directly
  using 192-bit outward-rounded Arb/ACB arithmetic over the whole declared transverse
  box, not merely at its centre or at the approximate root"。
- 数值改变：否。重跑 Arb：否。

### BR-07 — B_k 构造中混入 Taylor/order-30 语言 — **fixed**
- 位置：同 BR-05。
- 后：明确 "No Taylor truncation, order-30 jet, or local-jet reconstruction enters B_k."
- 数值改变：否。重跑 Arb：否。

### BR-08 — sup B_a < inf B_b ⟹ exact-root 严格次序的推理未显式 — **fixed**
- 位置：同 BR-05。
- 后：写出 sup B_a < inf B_b 蕴含对应 exact roots 的严格次序 ℐ̄(γ*_a)<ℐ̄(γ*_b)。
- 数值改变：否。重跑 Arb：否。

### BR-09 — 摘要/阅读指南混淆两个 66/66 — **fixed**
- 位置：`sec_front.tex` 摘要与 Reading guide。
- 前：frozen-point order-30 66/66 与 direct exact-root 66/66 未加区分。
- 后：摘要改为 mechanism certificate 52/66 box 比较、其 quartic-only 边界在序列化
  冻结十进制点上 34/66；Reading guide 列五行（34/66 point、66/66 frozen-point
  numerical diagnostic、52/66 box mechanism、66/66 box main、ρ≥0.95）并附两个 66/66
  的区分段落；prospective 指标为独立诊断，不进主定理。
- 数值改变：否。重跑 Arb：否。

### BR-10 — frozen-point 66/66 被表述为 "certifies" — **fixed**
- 位置：`sec_front.tex` Reading guide、`sec_back.tex` Table 1 与 Summary。
- 后：改述为 "point-valued numerical diagnostic … resolves 66/66 pair directions at
  the serialized frozen decimal points"，不再称为 exact-root box certificate。
- 数值改变：否。重跑 Arb：否。

### BR-11 — Table 1 缺 cohort 列与 point/box 区分 — **fixed**
- 位置：`sec_back.tex` Table 1（`tab:audits`）。
- 后：新增 Cohort 列；每行标明 point-valued / box-valued / rank；末行加粗为主定理
  （box）。排版用 \resizebox 适配 \textwidth。
- 数值改变：否。重跑 Arb：否。

### BR-12 — 34/66 quartic 边界的逻辑层级不清 — **clarified**
- 位置：`sec_back.tex` Table 1 行与表后段落、`sec_front.tex` 摘要。
- 后：标明 34/66 是序列化冻结十进制点上的 point-valued 低阶边界，不是 box 层。
- 数值改变：否。重跑 Arb：否。

### BR-13 — 产物路径错指 results/l4_order30/ — **fixed**
- 位置：`sec_back.tex` Summary 与 Table 2（`tab:cohortmap`）。
- 前：quartic 34/66 与 frozen-point order-30 66/66 被指到 `results/l4_order30/`。
- 后：改指 `results/l4_formal/`（真实冻结产物）；52/66 → `results/exact_root_ordering/`；
  66/66 main → `results/exact_root_ordering/`；12/12 roots →
  `results/exact_fibre_krawczyk/`；prospective → `results/g4_prospective/`。
- 数值改变：否。重跑 Arb：否。

### BR-14 — 缺 claim→cohort→产物映射表 — **fixed**
- 位置：`sec_back.tex` 新增 Table 2（`tab:cohortmap`）。
- 后：七层 claim 各映射 cohort、数学对象、artifact path、value type（point/box/rank）。
- 数值改变：否。重跑 Arb：否。

### BR-15 — cohort 漂移 6.05e-7 未披露 — **fixed**
- 位置：`sec_back.tex` Table 2 后段落。
- 后：披露 formal decimal cohort.json 与 l4_formal float64 候选之间 per-coordinate 至多
  6.05×10⁻⁷ 的漂移；明确其远小于所有区间半宽与 Δmin，"does not alter any strict
  inequality"，不改变 frozen theorem certificate。
- 数值改变：否（披露既有审计测得值）。重跑 Arb：否。

### BR-16 — prospective 20-path cohort 与 12-path formal cohort 混用 — **clarified**
- 位置：`sec_back.tex` Table 1、Table 2 及表后段。
- 后：三个 cohort（training 12-path、formal 12-path、prospective 20-path）分行列明、
  声明为不同冻结集合。
- 数值改变：否。重跑 Arb：否。

### BR-19 — P0 被读作严格包含的必要前提 — **fixed**
- 位置：`sec_mid.tex` Theorem 1 证明；`sec_back.tex` Appendix A 新增 Remark 3
  （`rem:p0role`，显示为 Remark 5）。
- 后：P0 改称 supplementary independent regularity check；严格包含仅由 v0.3.1 冻结
  Krawczyk 证书（192-bit Arb）建立。
- 数值改变：否。重跑 Arb：否。

### BR-20 — v0.3.2 被暗示为 v0.3.1 证明快照的一部分 — **fixed**
- 位置：`sec_back.tex` Code and Data Availability、Remark `rem:p0role`。
- 后：四个对象明确区分——v0.3.1 formal proof snapshot / v0.3.2 audit-closure
  supplement / 当前文稿文字修订 / 历史 DOI 对应旧 PDF；未虚构新 DOI。
- 数值改变：否。重跑 Arb：否。

### BR-21 — P1/P2 角色未写明 — **fixed**
- 位置：`sec_back.tex` Remark `rem:p0role`。
- 后：P0 = 生产 preconditioner 正则性的独立冗余核验（‖I−R_kC_k‖∞<1，Rump–Neumann）；
  P1 = 独立高精度模型重建；P2 = 解析/变异测试；三者加强可审计性，不替代、不修改、
  不构成 v0.3.1 冻结证明快照的一部分。
- 数值改变：否。重跑 Arb：否。

### BR-22 — "clean external reproduction" 措辞过强 — **fixed**
- 位置：`sec_back.tex` §10 Reproducibility。
- 后：改为 "clean-environment reproduction in fresh runtimes"，并明确两次运行均由
  作者在同一研究流程内执行，是内部可复现性检查，不是独立第三方复现。
- 数值改变：否。重跑 Arb：否。

### BR-23 — 跨架构执行的报告含糊 — **fixed**
- 位置：`sec_mid.tex` §4.2.2。
- 后：明确 n=2 次架构特定执行：arm64 参考环境 ρ=0.99398、top path pv17；
  x86_64/Rosetta ρ=0.98947、top path pv02；并声明 top path 非架构不变。
- 数值改变：否（从既有记录读取）。重跑 Arb：否。

### BR-24 — 12-path ρ=0.965035 被混同为 20-path 预注册 gate 的再次应用 — **fixed**
- 位置：`sec_back.tex` Table 1 表后段。
- 后：明确 0.965035 是 12-path covariance/ranking 审计的参考数值，不是 20-path
  prospective gate 的第二次应用；预声明 ρ≥0.95 gate 仅对独立 20-path cohort 适用一次。
- 数值改变：否。重跑 Arb：否。

### BR-25 — η 符号冲突（matching tolerance vs loss perturbation） — **fixed**
- 位置：`sec_front.tex` Definition `def:fibre`；`sec_mid.tex` §4/§5。
- 后：匹配容差改名 η_match（Ff_{η_match}），与 Corollary 1 的损耗扰动界 η 区分，
  并加消歧说明。
- 数值改变：否。重跑 Arb：否。

（BR-04、BR-17、BR-18 不在本轮委托清单内，维持原状：not applicable。）

---

## A 项（第一阶段清洁室审计）

### A1 — Figure 2 inset 遮挡 pv01/pv10/pv05/pv04 全局区间行 — **fixed**
- 位置：`scripts/generate_fig2_exact_root.py`（仅布局）；`fig2_exact_root.png` 重生成。
- 前：inset 位于中上区域，遮挡四条全局区间行标记。
- 后：inset 移至左下无数据内部 `[0.135, 0.14, 0.40, 0.32]`；其 y 轴刻度标签避开主 y
  轴路径标签，其 x 轴旋转刻度标签避开主 x 轴刻度标签。连通域检查 12/12 全局标记可见
  （10 蓝 + 2 红）。数据来源仍为 `exact_root_ordering_certificate.json`（字节不变），
  图中无任何冻结数据或最小间隙数值改变。
- 数值改变：否。重跑 Arb：否（仅重跑 matplotlib 绘图脚本，属排版修复）。

---

## B 项（第二阶段证明链审计）

### B14 — 显示值与证书值的舍入方向未声明 — **fixed**
- 位置：`sec_back.tex` Appendix B 开头（Rounding and hash conventions）。
- 后：声明全局舍入约定——下界向下、上界向上、负上界向零；显示值 Δmin=2.50×10⁻⁵ 是
  证书值 2.505874…×10⁻⁵ 的向下舍入；利用率以方向安全上界 0.866 引用，是计算最大值
  0.8653915… 的向上舍入；区间始终包含精确值。
- 数值改变：否。重跑 Arb：否。

### B15 — hash 算法、规范化序列化与 hash→文件映射未写明 — **fixed**
- 位置：`sec_back.tex` Appendix B 开头。
- 后：写明 SHA-256 作用于规范化 JSON 序列化（UTF-8、键排序、最小分隔符、无多余空
  白）、运行时元数据剔除，并给出五条 hash→文件路径映射（cohort / Krawczyk
  protocol / Krawczyk certificate / ordering protocol / ordering certificate）。
  五个前缀已与冻结文件独立重算核对一致。
- 数值改变：否。重跑 Arb：否。

---

## D 项（持续限制层）

### D1 — 单一两原子模型 — **documented residual**
- 位置：`sec_back.tex` §9 Limitations（Two atoms）。本轮未扩大模型范围；文字修订不
  改变该限制。数值改变：否。重跑 Arb：否。

### D2 — 无真实 PASQAL QPU/硬件证据 — **documented residual**
- 位置：`sec_back.tex` §9（No QPU evidence）。数值改变：否。重跑 Arb：否。

### D3 — 无第二独立区间实现 — **documented residual**
- 位置：`sec_back.tex` §9、§10（两次 clean-environment 运行声明为同一流程内部检查，
  不冒充第三方）。数值改变：否。重跑 Arb：否。

### D4 — Δmin 稳定窗窄 — **documented residual**
- 位置：`sec_mid.tex` Corollary 1（η<Δmin/2≈1.25×10⁻⁵，声明为严格的模型级要求）。
  数值改变：否。重跑 Arb：否。

### D5 — G4 精确排名/top path 非跨架构不变 — **clarified + documented residual**
- 位置：`sec_mid.tex` §4.2.2（n=2、两架构 ρ 与 top path 分列、非架构不变的明示）。
  数值改变：否。重跑 Arb：否。

### D6 — cohort 漂移 6.05e-7 — **fixed in text / documented residual in data**
- 位置：`sec_back.tex` Table 2 后段落（披露并论证不影响任何严格不等式）。冻结数据
  本身未改动。数值改变：否。重跑 Arb：否。

### D7 — 全局 fibre 结构/唯一性未证 — **documented residual**
- 位置：`sec_back.tex` §9（Global fibre structure）；Theorem 1 唯一性仅限声明盒内的
  措辞（BR-01）进一步收窄了表述。数值改变：否。重跑 Arb：否。

---

## E 项（v1.1 发布闭环审计）

### E4 — 引用与前向引用问题 — **fixed**
- 位置：`sec_back.tex` 文献 [7]（Arb）；`sec_front.tex` Lemma（原 Lemma 1 编号顺移）。
- 前：Arb DOI 误作 `10.1109/TC.2017.269063`；某 Lemma 含对后文编号公式的前向引用。
- 后：DOI 更正为 `10.1109/TC.2017.2690633`；前向编号引用改为对 §4（`sec:quartic`）
  的文字指路；Krawczyk 严格包含的存在/唯一性依据保持 Tucker/Moore 等标准引用 [9,
  10, 20]；新增对称基归一化的显式声明（{|gg⟩,(|gr⟩+|rg⟩)/√2,|rr⟩）。
- 数值改变：否。重跑 Arb：否。

---

## 定点复核修复（打包与一处数值引用，2026-08-12 第二轮）

在交付后的定点复核中发现三项非数学、非证书问题，已全部修复：

1. **利用率引用方向安全性**（文字层）：Theorem 1 证明中的
   `max_k ‖K_k(X)‖∞/3×10⁻¹² = 0.865 < 1` 改为 `< 0.866 < 1`；Remark 2 中 "utilization
   0.865" 改为 "utilization bound 0.866"；Appendix B 舍入约定改为"0.866 是计算最大值
   0.8653915… 的向上舍入，方向安全地高于认证最坏利用率"，并说明上界引用（而非截断
   等式）才是正确形式。不再出现 "=0.865"。不涉及证书改动。
2. **构建说明**：BUILD_README.md 改为 canonical build = XeLaTeX ×3、预期 24 页 A4；
   注明 pdfLaTeX 可能给出排版等价的 23 页布局、不是 canonical freeze build；Tectonic
   （XeTeX/xdvipdfmx 路线）与 canonical 一致，本包冻结 PDF 即由其产出。
3. **修订日志入包**：本 REVISION_LOG_v1.2.md 已纳入 source ZIP 并计入其内部
   SHA256SUMS.txt manifest。

修复后重新编译 ×3、重生成 PDF/ZIP/内部哈希；下方验证记录已更新。

---

## 第三轮定点修复（附件盲审确认项，2026-08-12）

依据刚完成的附件盲审，仅关闭已确认的文字、记号和排版问题；未重组论文、未扩大
结论、未修改正式计算资产。逐项记录（编号按盲审单）：

### A-2 — Krawczyk 算子类型一致性 — **fixed**
- 位置：`sec_mid.tex` §6.1（Eq. (26) `eq:krawczyk`、centered 形式、Theorem 1、
  computer-assisted proof、Remark 2）；`sec_back.tex` Appendix A。
- 旧：Krawczyk 算子写成 K(X)=x₀−CF(x₀)+(I−C[DF(X)])(X−x₀)，把 x∈R¹⁶ 直接传给
  F:R²⁴→R¹⁶，类型不成立。
- 新：统一为路径相关形式 K_k(X)=x₀−C_kF_k(x₀)+(I−C_k[DF_k(X)])(X−x₀)，centered
  x₀=0 时为 K_k(X)=−C_kF_k(0)+(I−C_k[DF_k(X)])X；新增 Eq. (25) `eq:reducedjac`
  显式给出 DF_k(x)=DF(γ̂_k+N_kx)N_k∈R¹⁶ˣ¹⁶；C_k 明确为相应 reduced midpoint
  Jacobian 的冻结 point preconditioner；并声明 "at no point is a transverse vector
  x∈R¹⁶ passed directly to F"。
- 数值改变：否。证书改变：否。重跑 Arb：否。

### A-3 — cohort drift 的方向安全上界 — **fixed**
- 位置：`sec_back.tex` Summary（Table 2 后段落）；本日志 BR-15/D6 条目。
- 旧："differ by at most 6.05×10⁻⁷ per coordinate"（记录最大值 6.0520531…×10⁻⁷，
  6.05e-7 不是有效上界）。
- 新："differ by less than 6.06×10⁻⁷ per coordinate (max|Δγ|<6.06×10⁻⁷)"，并注明
  6.06e-7 是对记录值 6.0520531…×10⁻⁷ 的方向安全向上引用；明确该漂移不改变任何
  certified interval inequality 或 theorem-bearing certificate。JSON 未改。
- 数值改变：否（仅引用方式）。证书改变：否。重跑 Arb：否。

### A-7 — Dyson tail 的数学对象 — **fixed**
- 位置：`sec_mid.tex` Proposition 2；`sec_back.tex` Appendix A；本日志相关条目。
- 旧："the analytic even Dyson tail after order thirty is enclosed by 2×10⁻¹¹"（未区分
  mean tail 与 per-axis tail）。
- 新："the mean six-axis analytic even Dyson tail after order thirty is enclosed by
  2×10⁻¹¹"（记录 mean_tail 1.2342576…×10⁻¹¹，与打包 JSON
  `results/exact_root_ordering/exact_root_ordering_certificate.json` 一致），并补
  "the largest individual-axis tail is below 4×10⁻¹¹"（记录最大 axis_tail
  3.7027728…×10⁻¹¹，已由打包 JSON 直接确认）。摘要/结论不涉及数值 tail，无需改。
- 数值改变：否（从冻结 JSON 读取）。证书改变：否。重跑 Arb：否。

### A-8 — P0 冗余核验的显式说明 — **clarified**
- 位置：`sec_mid.tex` Theorem 1 computer-assisted proof 末尾。
- 新：加入"In the strict-inclusion form of the Krawczyk theorem used here, the required
  regularity is already implied by the accepted inclusion; the v0.3.2 P0 certificate is
  therefore an independent redundant audit of the production preconditioner, not an
  additional premise of Theorem 1."未新增文献（未能现场确认完整书目信息，按要求只补
  文字）。
- 数值改变：否。证书改变：否。重跑 Arb：否。

### B-4 — Table 2 映射补全 — **fixed**
- 位置：`sec_back.tex` Table 2（`tab:cohortmap`）。
- 新：新增两行——Covariance contraction ranking（12-path covariance cohort、
  contraction rank、`results/l3_covariance/`、rank）与 P0 preconditioner audit
  （v0.3.2 supplement、redundant regularity、`results/audit_closure/`、audit）；表后
  注明前者是 rank 诊断（记录 ρ=0.965035）、后者是 v0.3.2 独立冗余正则核验、不是主
  定理新前提。Table 1 数值未动。
- 数值改变：否。证书改变：否。重跑 Arb：否。

### B-5 — projective constraint map 定义域 — **fixed**
- 位置：`sec_front.tex` §3.2 Eq. (12) 之后。
- 旧：全局写法 F:R²⁴→R¹⁶。
- 新：明确 F:U→R¹⁶，U={γ∈R²⁴: ψ_{γ,0}(0)≠0} 为 chart-valid open set，后文的
  R²⁴ 写法为此限制的简写；并说明 formal accepted transverse boxes 经形式验证均
  包含于 U（chart 分母在每个 accepted box 上排除零）。
- 数值改变：否。证书改变：否。重跑 Arb：否。

### B-10 — 完整根盒量词移入 Theorem 2 陈述 — **fixed**
- 位置：`sec_mid.tex` Theorem 2（`thm:ordering`）陈述。
- 旧：根盒包含式只在证明中。
- 新：定理陈述直接包含 B_k⊇{ℰ̄(γ̂_k+N_kx): x∈[−3×10⁻¹²,3×10⁻¹²]¹⁶}（"covering
  the complete root box"）；证明中的解释保留未删。
- 数值改变：否。证书改变：否。重跑 Arb：否。

### B-12 — Figure 2 脚本 endpoint radius 处理 — **fixed**
- 位置：`scripts/generate_fig2_exact_root.py`（解析逻辑）与 docstring。
- 旧：Arb 端点串 `[mid ± radius]` 只取 mid 作为端点。
- 新：解析 midpoint 与 radius，下端用 mid−radius、上端用 mid+radius（向外端点），
  disjointness 与 minimum gap 均按 outward endpoints 判断；docstring 注明端点半径
  （~1e-58）比最小间隔小 50 个以上数量级。重生成后校验全部通过：路径顺序不变、
  66/66 不变、minimum pair 仍 pv08→pv11、full-precision gap
  2.5058740347192478808…×10⁻⁵、显示值仍方向安全 2.50e-5、PNG 与前一版本字节一致
  （`743ee774…c6a6`，视觉内容不变）。冻结 JSON 未改。
- 数值改变：否（计算结果不变）。证书改变：否。重跑 Arb：否。

### C-4 — Figure 1 TikZ 排版 — **fixed**
- 位置：`sec_front.tex` Figure 1（`fig:schematic`）TikZ 源码（仅排版）。
- 新：t=−1/t=+1 标签加白色背景与小 inner sep；panel (a) transverse-box 红标签移至
  下方并缩短、不再侵入 panel (b)；numerical tangent 标签独立置位不再被引线穿过；
  local numerical continuation 标签下移与红标签分开。示意图数学含义不变，Figure 2
  未动。
- 数值改变：否。证书改变：否。重跑 Arb：否。

### D-10 — 版本命名说明 — **fixed**
- 位置：`sec_back.tex` Appendix C。
- 新：加入"The 'v1.3 pipeline' denotes the formal reproduction script generation used
  by the certificate snapshot frozen at repository tag v0.3.1; it is distinct from
  manuscript version v1.2 and from the audit-closure tag v0.3.2."（与现有文本及仓库
  tag v0.3.1/v0.3.2 核实一致，未新增未经证实的 tag 关系）。
- 数值改变：否。证书改变：否。重跑 Arb：否。

### D-11 — BUILD_README 页数与构建说明 — **clarified**
- 位置：`BUILD_README.md`。
- 新：页数更新为 25 页（本轮定点修复后；此前候选为 24 页）；canonical build 仍为
  XeLaTeX ×3；pdfLaTeX 仍注明为非 canonical 的排版等价路线。
- 数值改变：否。证书改变：否。重跑 Arb：否。

修复后重新编译 ×3、重生成 PDF/ZIP/内部哈希；下方验证记录已更新。

---

## 验证记录（本轮执行）

- 编译：canonical XeTeX/xdvipdfmx 路线 ×3（本环境以 tectonic 0.15.0 执行，与 XeLaTeX
  同引擎路线）；undefined references = 0；undefined citations = 0；rerun warnings = 0；
  overfull hbox/vbox = 0；underfull hbox/vbox = 0；页数 25（与 canonical XeLaTeX 路线
  一致）；公式编号 (1)–(27) 连续（第三轮新增 Eq. (25) `eq:reducedjac`）；引用编号
  [1]–[20] 连续（未新增文献）。
- Figure 2：无遮挡、无标签碰撞；12/12 全局标记可见；冻结数据不变；PNG 与第二
  轮字节一致（outward endpoint 修正不改变任何像素）。
- Figure 1：t=±1 白底、红标签不侵入 panel (b)、tangent 与 continuation 标签不被
  引线穿过或互相重叠；示意图数学含义不变。
- PDF 与 source ZIP 内 PDF 字节一致（SHA-256 见文末交付报告）。
- source manifest：`SHA256SUMS.txt` 全部 OK（仅新 source package 自有 manifest，
  仓库根 manifest 未触碰）。
- 语义 diff：新旧 PDF 数值记号多重集差异仅为已批准修复（0.98947/0.99398 精确化、
  利用率方向安全上界 0.866（计算值 0.8653915…）、2.505874 全值、cohort 漂移方向
  安全上界 6.06e-7（记录值 6.0520531…e-7）、mean six-axis tail 2e-11 与 per-axis
  <4e-11 区分（记录值 1.2342576e-11 / 3.7027728e-11）、Arb DOI 更正、v0.3.1/v0.3.2
  版本指路）；无任何证书数值变化。
- 只读回归（仓库克隆，git status 干净）：
  - `python tools/verify_reference_results.py` — 全部 PASS（Krawczyk gates、ordering
    gates、two-run determinism、dissipative summary、reference artifacts）；
  - `python -m unittest discover -s tests -v` — 退出码 0；
  - `sha256sum -c SHA256SUMS.txt` — 0 失败。
- 旧附件 manuscript.pdf SHA-256 仍为
  `32ae60ac2af51a7b05babce2ad7647890ad8c80023fa96647cceeb31db5f189f`；正式证书、
  JSON、代码 0 字节变化；未 commit、push、tag、Release 或操作 Zenodo。

---

## 第四轮定点修复（v1.2.1：一处论文数值更正 + 一处 provenance 状态关闭，2026-08-12）

**版本关系**：v1.2.1 取代 v1.2 freeze candidate；与 v1.2 的差异仅为以下两处，其余
（定理、证明、证书、JSON、图、数值门）逐字节相同。v1.2 candidate 不被覆盖，保留在案。

### G-1 — §4.2.2 过期拟合残差数值 — **fixed**
- 位置：`sec_mid.tex` §4.2.2 段末。
- 旧："the maximum local fit residual was 1.48×10⁻¹⁰"（来自已被替换的旧 artifact）。
- 新："the maximum relative fit residual was 2.37×10⁻¹⁰, the direction-safe upward
  rendering of the frozen field `maximum_relative_fit_residual` in
  `results/g4_prospective/report.json`"（冻结字段值 2.3662077377223515e-10 < 2.37e-10，
  方向安全）。同段两个 Spearman ρ、top path、cohort 数量、平台说明、gate 结论均未改；
  全文搜索 1.48 / 1.4811206848913056e-10 已为 0 次。
- 数值改变：仅这一处过期值更正（文字层）。证书改变：否。重跑 Arb：否。

### G-2 — g4_prospective provenance 过期状态关闭 — **fixed**
- 位置：仓库 `results/g4_prospective/provenance.json`（status 字段）。
- 旧："legacy manuscript sample pending paper correction"。
- 新："legacy manuscript sample corrected in v1.2.1 textual revision"。
- 同步：`tools/verify_reference_results.py` 中对应断言更新；仓库根 `SHA256SUMS.txt`
  两个受影响条目（provenance.json、verify_reference_results.py）就地更新；
  `sha256sum -c` 0 失败，`python tools/verify_reference_results.py` 全部 PASS，
  `python -m unittest discover -s tests` 退出码 0。未修改
  original_colab_sample.mean_spearman=0.996992、prospective report 任何结果、
  protocol/cohort/ranking certificate 或外部验证数据。该修复不是新实验、证书重跑或
  数学结果。
- 数值改变：否（状态字段文字）。证书改变：否。重跑 Arb：否。

### 保留为 documented residual（本轮不处理）
ψ₀ 下界未序列化；v0.3.2 为 lightweight tag；covariance audit 的 pv01–pv12 标签复用；
未引用的 LaTeX labels。（"旧图脚本只读取 midpoint" 一项已在第三轮 B-12 修复。）

### 验证（本轮执行）
- canonical XeTeX 路线 ×3（tectonic）：undefined refs/cits = 0；rerun = 0；
  overfull/underfull = 0；页数 25；公式 (1)–(27) 连续；引用 [1]–[20] 连续。
- Figure 2 PNG 与 v1.2 字节一致（`743ee774…c6a6`）；冻结证书 JSON 字节一致
  （`1e0bb221…7d42`）。
- 论文文本 diff：除 §4.2.2 目标句外无非机械性变化；provenance.json 除 status 字段
  外无变化；theorem-bearing assets 0 字节变化。
- 未进行任何 commit、push、tag、Release 或 Zenodo 动作。
