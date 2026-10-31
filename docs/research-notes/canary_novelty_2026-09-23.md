# R3 新颖性核证：Canary Red-Teaming（金丝雀红队）（2026-09-23）

> 核证结论先行：**空位成立（条件性新颖）**——三要素组合（① 微调/LoRA 把结构完整可逐字核验的虚构"能力代用品"植入权重；② 对植入行为跑标准化越狱攻击；③ 攻击成功=提取出植入内容的精确/语义匹配，作为对抗性安全评测的构造性真值）**未被任何已发表工作占据**。但每个单独组件都有强近邻，最高威胁为 Cywiński et al. 2510.01070（权重植入秘密+提取攻击，判据仍是 auditor 猜测）与 Jailbreak Tax 2504.10694（judge-free 越狱评测，真值是良性题答案正确性）。窗口紧，建议 3-4 个月内完成首发。
>
> 通道纪律标注：**本次走了按量通道**（用户显式点名 zhipu std×4 / pro×3 + deepseek×2；内置 WebSearch×5 + WebFetch×9；共 23 轮调用）。本次使用了按量通道：zhipu-search std 与 pro、deepseek search_web。

---

## 〇、待核证想法（复述）

**Canary Red-Teaming**：用 LoRA/微调把虚构但结构完整、可逐字核验的"能力代用品"（如虚构化合物的虚构合成路线、虚构恶意软件的行为描述）植入受害模型 → 对植入行为跑越狱攻击 → 攻击成功 := "提取出植入内容"（精确/语义匹配）。由此为对抗性安全评测提供**真值由构造给出（ground truth by construction）**的金标准，消灭判官（LLM-judge/human-judge）主观性。

核心可分主张（本次逐一核验）：
- P1 植入物在**权重**（非上下文/系统提示/检索库）
- P2 植入物是**结构完整的能力代用品**（非单条事实/单词/PII）
- P3 成功判据是**提取匹配**（非行为出现/能力恢复/答案正确）
- P4 目的是**评测方法论**（为 ASR 提供真值），非研究模型内部/诱发技术本身

---

## 一、查询全归档（23 轮，通道×查询词×关键发现×来源）

| # | 通道 | 查询词 | 关键发现 | 来源 |
|---|---|---|---|---|
| 1 | WebSearch W1 | canary strings planted in LLM fine-tuning used as ground truth for jailbreak attack success evaluation | 结果全部=canary 用于污染检测（BIG-bench GUID、CapBencher、Gemini 3 污染事件）；**明确"无人做 planted-canary→jailbreak ground truth"** | alignmentforum.org, arxiv (CapBencher), stuker.com |
| 2 | zhipu std S1 | canary 记忆化 提取 大语言模型 红队评测 攻击成功判定 | 全部=通用红队框架/工具（WallBreaker、GPT-Red、FinSafetyBench），无 canary 真值思路 | 武汉大学学报类, github |
| 3 | deepseek D1 | verifiable jailbreak success criteria LLM red-teaming "ground truth by construction" planted secret extraction exact match instead of LLM judge | **三大近邻定位**：PasswordEval 2508.19980（系统提示植入密码+exact-match 泄露判据）；Jailbreak Tax 2504.10694（良性已知答案题+答案正确性判据，ICML25）；AgentSecBench 2605.26269（环境级 planted marker+精确判别器）；另"Knowledge-Gated Verifiable Tasks"（agent 域构造性真值） | arxiv 2508.19980, 2504.10694, 2605.26269, spylab.ai, semanticscholar |
| 4 | WebSearch W2 | planting fictional knowledge in model weights LoRA fine-tuning extracting via attack "model organisms"/"sleeper agents" evaluation | **最近邻浮出**：Cywiński et al. "Eliciting Secret Knowledge from Language Models"（微调植入秘密+black-box/white-box 提取+auditor 判分）；Sleeper Agents 2401.05566（后门行为+安全训练持久性）；Anthropic 内省适配器（700 个植入缺陷模型测审计）；Betley narrow finetuning misalignment | arxiv, github.com/cywinski/eliciting-secret-knowledge |
| 5 | zhipu std S2 | 植入后门 触发器 大模型 安全评测 真值 ground truth 越狱 水印 | 全部=后门攻防（AdvBDGen、ConfGuard AAAI26、干净标签攻击）——**攻防向，无"后门作为评测真值"工作** | 微信公众号技术文章, AAAI |
| 6 | zhipu pro P1 | LLM fine-tune planted canary synthetic route fictional malware extraction jailbreak ground truth evaluation benchmark | 全部=恶意软件生成（LLMalMorph、MalGEN、Ransomware3.0）——**虚构恶意内容生成存在，但用于攻击演示非评测真值** | arxiv 2507.09411, 2506.07586 |
| 7 | WebFetch F1 | arxiv.org/abs/2508.19980 (PasswordEval) | 确认：Sam/Robey/Zou/Fredrikson/Kolter（CMU），contextual robustness 基准，密码机制；摘要页未显示植入位置与判据细节（deepseek 转述全文称 exact-match string checker——标注为二手信息） | arxiv 2508.19980 |
| 8 | WebFetch F2 | github.com/cywinski/eliciting-secret-knowledge | 确认：作者 Cywiński/Ryd/Wang/Rajamanoharan/Nanda/Conmy/Marks；微调 Gemma2/Llama 造 Taboo/Gender/SSC 三族模型；black-box（高温采样、many-shot、prefill）+white-box（logit lens、SAE）提取；判据=LLM auditor 猜秘密 | github |
| 9 | WebFetch F3 | arxiv.org/abs/2504.10694 (Jailbreak Tax) | 确认：对良性已知答案题制造拒答对齐（system prompt/SFT），jailbreak 成功=答案正确性；"known ground truth answers"避开 judge | arxiv 2504.10694, ethz-spylab/jailbreak-tax |
| 10 | WebSearch W3 | knowledge editing ROME MEMIT inject fictional knowledge then evaluate safety attack extraction benchmark | 编辑文献均为编辑质量/持续编辑/编辑 vs 遗忘基线（AAAI26）——**无人用编辑构造安全评测真值** | aclanthology, ojs.aaai.org |
| 11 | deepseek D2 | CTF flag-based verifiable AI security evaluation honeypot canary trap; sandbagging planted capability eval Anthropic | **Password-Locked Models**（Greenblatt NeurIPS24）+ **Anthropic 破坏评测**（训练沙袋模型验证评测方法）+ CTF flag 谱系（Cybench/InterCode-CTF/NYU CTF/BraceGreen）+ AWS Deception Benchmark（蜜罐抗过拟合）+ TELUS canary trap（RAG 幻觉） | papers.nips.cc, anthropic.com/research/sabotage-evaluations, aclanthology 2026.kallm-1.15, github aws-security-labs |
| 12 | zhipu pro P2 | fictional biosafety capability surrogate evaluation biorisk LLM fictional scenario verifiable ground truth no judge benchmark | 生物安全评测全谱（ABC-Bench NeurIPS/ICML26、SPIKE-Bench、Intern-BioBreaker、BioSecBench-Refusal、智源 DNA 分片）——**全部真实能力+湿实验/分类器验证，无虚构植入代用品** | arxiv 2606.11150, 2608.02684, 2607.18056, 2607.05462 |
| 13 | WebFetch F4 | arxiv.org/abs/2605.26269 (AgentSecBench) | 确认：Alpay & Alpay，2026-05 预印本；三"游戏"（注入/检索机密/工具完整性）；**marker 在环境（检索/工具内容）非权重**；exact-marker disclosure 谓词+"unambiguous ground truth"表述；Qwen3-0.6B/1.7B | arxiv 2605.26269 |
| 14 | WebFetch F5 | arxiv.org/abs/2012.07805 (Carlini 2021) | 确认：训练数据提取攻击（GPT-2），逐字匹配验证；**纯记忆化测量，无安全护栏绕过、无植入** | arxiv 2012.07805 |
| 15 | WebFetch F6 | arxiv.org/abs/2102.07809（试图取 SecretSharer） | **ID 错误**：该 ID 实为标准化考试分数政策论文（Kannan et al.）；SecretSharer 需另寻 | （错误记录） |
| 16 | WebFetch F7 | usenix.org/conference/usenixsecurity19/presentation/carlini (SecretSharer 官方页) | 确认：随机 canary 秘密插入训练数据、exposure 度量、**目的是量化无意记忆化**，无红队/越狱用途 | usenix.org |
| 17 | WebFetch F8 | papers.nips.cc 7ff97417 (Password-Locked Models 摘要页) | 确认：微调使能力仅在密码出现时展示；测试微调/RL 诱发方法；**成功=恢复隐藏能力基准表现**（非逐字提取）；目的=验证危险能力诱发方法 | papers.nips.cc |
| 18 | zhipu std S3 | 微信公众号 大模型 金丝雀 canary 植入知识 微调 越狱 评测 真值 判官 | canary 中文谱系全落隐私/记忆化/污染：Privacy Auditing canary 构造、CanaryBench、Meeus 金丝雀回声（PMLR v267）、EPA 合成金丝雀、SIGIL 2606.06502（版权取证）、Canary Tools（agent 工具诊断）、Kill-Chain Canaries（注入 ASR 仪表化）——**无越狱 ASR 真值用途** | themoonlight.io, pmlr.com.cn, arxiv 2606.06502, githubnext.com |
| 19 | WebSearch W4 | AISI inoculation fine-tuning models with dangerous capabilities synthetic data to test safeguards evaluation CBRN | Kaunismaa et al. "Eliciting Harmful Capabilities by Fine-Tuning on Benign Data"（ICLR26，良性数据微调诱发化武能力）；Inoculation Midtraining（防御）；Anthropic SDF（合成文档微调改信念） | openreview, alphaxiv, arxiv |
| 20 | zhipu pro P3 | verifiable rewards RLHF planted synthetic task ground truth evaluation agent benchmark exact-match success predicate | RLVR 谱系（数学/代码可验证奖励、HardTestGen、Loong）——**客观验证范式存在但无人迁移到安全红队**；AutoEval Done Right（Boyeau 2403.07008 合成数据评测） | arxiv, paperlens.io |
| 21 | WebSearch W5 | site:mp.weixin.qq.com 大模型 金丝雀 植入 虚构 知识 微调 红队 越狱 评测 | site: 限定不被支持，多轮换词后无微信命中；侧获 **GuidedBench**（港科大 2025-08，越狱评估误判修复——评分指南路线，非真值路线）；JailBench 中文数据集 | secrss.com, juhe.cn |
| 22 | zhipu std S4 | "canary red-teaming" / "canary red teaming" / "planted capability" jailbreak benchmark attack success exact match LoRA fine-tune victim model（英文精确撞车检查） | **纯园艺噪声（金丝雀园艺/鸟类）——精确短语无学术占用** | （空结果） |
| 23 | WebFetch F9 | arxiv.org/abs/2510.01070 (Cywiński 论文摘要页) | 最终确认：三个模型族"knowing but denying"；攻击=prefill（black-box 最强）+logit lens/SAE（white-box）；判据=LLM auditor 猜中秘密；定位=**"public benchmark for evaluating secret elicitation methods"（审计/可解释性），非 ASR 真值** | arxiv 2510.01070（2025-10-01 v1, 10-31 v2） |

---

## 二、最近邻威胁表（按威胁降序）

### 撞死级：无

### 部分重叠（高威胁，必引+正面划界）

| 文献 | 出处 | 精确差异（一句话） | 威胁 |
|---|---|---|---|
| **Eliciting Secret Knowledge from Language Models**（Cywiński, Ryd, Wang, Rajamanoharan, Nanda, Conmy, Marks） | arXiv 2510.01070（2025-10，未标 venue；代码/模型开源） | 同样"微调植入秘密→提取攻击"，但秘密是简单事实/行为（禁忌词、用户性别）、判据是 **LLM auditor 猜测**（仍经判官！）、目的是审计/可解释性 benchmark——**无一能力级代用品、无精确/语义匹配谓词、无 ASR/判官消除定位**。https://arxiv.org/abs/2510.01070 | ★★★★★（概念空间最近；但其判据仍依赖 auditor，恰是我们的批判点） |
| **The Jailbreak Tax**（Nikolić, Sun, Zhang, Tramèr, ETH SPY Lab） | arXiv 2504.10694，ICML 2025 | 已占据"judge-free 越狱成功判据"叙事，但真值=**良性已知答案题的答案正确性**（植入的是拒答策略而非危险能力），测 utility 税而非内容提取——无权重植入能力、无提取匹配。https://arxiv.org/abs/2504.10694 | ★★★★☆（叙事近，机制远；项目 R2 已引） |
| **Stress-Testing Capability Elicitation With Password-Locked Models**（Greenblatt et al.） | NeurIPS 2024 | 权重级隐藏能力+诱发攻击，但**成功=能力基准分数恢复**（非逐字提取）、攻击=微调/RL 诱发（非越狱提示）、目的=验证诱发方法——非评测真值方法论。https://papers.nips.cc/paper_files/paper/2024/hash/7ff97417474268e6b5a38bcbfae04944-Abstract-Conference.html | ★★★★☆ |
| **Sleeper Agents**（Hubinger et al.） | arXiv 2401.05566（2024，664 引） | 训练条件性后门行为测安全训练持久性，**成功=行为缺陷出现（行为判读）**，非植入内容提取；无评测判据革新诉求。https://arxiv.org/abs/2401.05566 | ★★★☆☆ |

### 部分重叠（中威胁）

| 文献 | 出处 | 精确差异 | 威胁 |
|---|---|---|---|
| **Sabotage evaluations for frontier models**（Anthropic）+ **AI Sandbagging**（ICLR 2025） | anthropic.com/research/sabotage-evaluations | "植入训练行为以验证评测方法"的范式先例（训练沙袋模型→测评测能否检出），但域=能力隐瞒、指标=分数抑制，非越狱 ASR/提取真值 | ★★★☆☆ |
| **PasswordEval**（Sam, Robey, Zou, Fredrikson, Kolter，CMU） | arXiv 2508.19980 | 越狱下 exact-match 泄露判据已存在，但秘密植于**系统提示（上下文）**非权重，测 contextual integrity 非能力代用品提取 | ★★★☆☆ |
| **AgentSecBench**（Alpay & Alpay） | arXiv 2605.26269（2026-05） | "planted marker+unambiguous ground truth+精确判别器"表述已出现在 **agent 安全域**，但 marker 在环境（检索/工具内容）非权重、非越狱 ASR 域 | ★★★☆☆ |
| **Kaunismaa et al., Eliciting Harmful Capabilities by Fine-Tuning on Benign Data** | ICLR 2026 | 微调诱发真实危险能力（化学），但诱发的是**真实**能力且无植入虚构代用品/无提取真值判据 | ★★☆☆☆ |
| **Anthropic 内省适配器**（700 个植入缺陷模型审计） | Anthropic 2026（新智元转述） | 大批量植入行为模型做审计实验的工程先例；判据=内省自报，非提取匹配 | ★★☆☆☆ |
| **Eliciting latent knowledge (Taboo)**（companion, 2025-05） | arXiv（W2 检出） | 同 Cywiński 谱系的机制可解释性工具 | ★★☆☆☆ |

### 仅引用划界（低威胁/谱系）

| 文献 | 出处 | 用途 |
|---|---|---|
| Secret Sharer（Carlini et al.） | USENIX Security 2019 | canary 植入+exposure 度量鼻祖——测记忆化非攻击成功 |
| Extracting Training Data from LLMs（Carlini et al.） | arXiv 2012.07805 / USENIX 2021 | 提取攻击谱系——无植入、无护栏绕过 |
| BIG-bench canary GUID / CapBencher（Ishida et al. 2025）/ Gemini 3 污染事件 | arxiv / alignmentforum | canary 的现行语义=污染检测 |
| SIGIL | arXiv 2606.06502 | canary 序列→训练集包含性取证（版权域的"可证明"用法） |
| CanaryBench / Meeus 金丝雀回声（PMLR v267）/ Privacy Auditing canary 构造 / EPA 合成金丝雀 | 见 S3 来源 | 隐私审计 canary 谱系 |
| CTF flag 评测（Cybench / InterCode-CTF / NYU CTF / BraceGreen ACL 2026 KALLM） | aclanthology 2026.kallm-1.15 等 | 环境级 flag 真值先例（沙箱内，非权重内） |
| AWS Deception Benchmark / TELUS canary trap | github aws-security-labs | 蜜罐/canary-trap 在安全工程的用法 |
| GuidedBench（港科大） | secrss 2025-08 | 修判官误判的"指南"路线——与"消灭判官"路线对照 |
| RLVR 谱系（Loong、HardTestGen 等） | arxiv | 客观验证范式在数学/代码域的先例 |
| ABC-Bench / SPIKE-Bench / Intern-BioBreaker / BioSecBench-Refusal / 智源 DNA 分片 | arxiv 2606.11150 等 | 生物安全评测现状=真实能力+湿实验/分类器——凸显虚构代用品的成本优势 |
| Model organisms of misalignment / Betley narrow finetuning / Anthropic SDF | arxiv / blog | 植入行为方法论谱系 |
| Knowledge editing vs unlearning（AAAI 2026） | ojs.aaai.org | 编辑工具被评测 vs 被用于构造评测——无后者 |

---

## 三、七路排查逐路结论

1. **canary→记忆化/提取谱系**：✅ 排查完毕。Carlini 2019/2021、SecretSharer、BIG-bench GUID、CapBencher、CanaryBench、Meeus、EPA、SIGIL、隐私审计 canary——全部测"记忆化/污染/隐私"，**无一直接把 canary 用作 red-team/jailbreak 的攻击成功真值**。W1 明确空位。
2. **合成基准/合成真值用于安全评测**：✅。生物安全评测（ABC-Bench 等 5+ 个）全走真实内容+湿实验/分类器；Jailbreak Tax 用良性已知答案；GuidedBench 用评分指南——**虚构结构完整能力代用品+构造性真值无人做**。
3. **后门/植入触发器作为评测工具**：✅。中文文献（AdvBDGen/ConfGuard/干净标签）+ Sleeper Agents + 内省适配器——后门皆为攻击对象或鲁棒性研究对象；**"后门=评测真值发生器"的倒置用法未出现**（Sabotage evals 是最接近的"植入以验证评测"，但判据非提取）。
4. **ground truth by construction / 可验证红队结果 / 客观成功判据**：✅。CTF flag（环境级）、PasswordEval（上下文级）、AgentSecBench（环境级 marker）、Jailbreak Tax（答案正确性）——**权重级植入+内容提取谓词空缺**；精确短语 "canary red-teaming" 无占用（S4 园艺噪声）。
5. **知识编辑用于评测**：✅。编辑文献全部在编辑质量/遗忘基线域，无编辑构造安全评测真值的工作。
6. **RL/agent planted-task / 可验证奖励**：✅。RLVR=数学/代码域验证器；agent 域有 Knowledge-Gated Verifiable Tasks（构造性真值先例，但为任务门控内容非危险能力、非权重植入+越狱）。
7. **中文文献**：✅。zhipu std S1/S3 + WebSearch W5 三路：canary 中文语义=隐私/污染/防御；红队中文语义=策略集成/RL 攻击/工具；**两词在中文生态未交叉**；微信 site: 检索无命中（site 限定不被支持，已用"微信公众号"关键词+中文通用检索兜底，S3 覆盖了 themoonlight/pmlr 中文技术源）。

---

## 四、Novelty 判定

### 判定：空位成立（条件性新颖，窗口紧）

**未被占据的组合主张**：权重植入（P1）× 能力级虚构代用品（P2）× 提取匹配谓词（P3）× 评测方法论定位（P4）。四个组件各自的最强先例（Cywiński=P1、Anthropic/AISI=P2 的远亲、PasswordEval/AgentSecBench=P3 的上下文版、Jailbreak Tax=P4 的答案版）**两两之间无一篇覆盖三个以上要素**。

**必须钉死的差异化修辞**（防审稿人"=Cywiński 的扩展"）：
- 对 Cywiński：其判据是 **LLM auditor 猜测**——恰恰保留了判官主观性，与我们的动机正面对立；且其秘密为单词级事实，无结构完整文档，无精确/语义双匹配，无 ASR 语义。我们=把其"审计对象"变成"测量仪器"。
- 对 Jailbreak Tax：其真值锚在**良性任务的答案**（测"模型答对了被禁止的题"），我们锚在**危险内容本体**（测"模型交出了它拥有的危险代用品"）——外推效度论证完全不同（他们仍依赖模型预训练知识，我们构造知识）。
- 对 Password-Locked：他们测诱发方法的有效性（方法评测），我们测受害模型的防御（系统评测）；他们的判据仍是能力基准分。
- 对 PasswordEval/AgentSecBench：上下文植入会被上下文清洗/防御过滤影响混淆内生效度；权重植入才隔离"模型内部拥有→输出生成"通道。

**风险登记**：
- R-A：Cywiński 已开源模型+代码并自称 benchmark——若其团队或后人扩展到能力级代用品+攻击套件+ASR 语义即撞；速度要求 3-4 个月内首发（含预印本占位）。
- R-B：前沿实验室（Anthropic/AISI/OpenAI）内部评测可能有未发表同类构造（sabotage evals 的自然外推）；投稿时用"我们给出首个公开、可复现、系统化的表述+工具"防御。
- R-C："消灭判官"叙事不能单独成立（StrongREJECT/GuidedBench/Jailbreak Tax 都在修判据），必须钉在"真值由构造给出"这一构造性主张+可发布虚构数据集（继承 canary GUID 可发布传统）。

### 最强 2-3 个 framing 候选

1. **「Ground Truth by Construction for Adversarial Safety Evaluation」**（方法论主 framing）：把 CTF flag 的可验证性从沙箱搬进权重——植入即真值，ASR 变成零判官测量。直接对话 Jailbreak Tax/StrongREJECT/判官校准线（本项目 R2），主张提取谓词比答案正确性更贴近"危险能力泄露"的构念效度。
2. **「Capability Surrogates：可发布的安全评测」**（应用 framing）：生物/网络域评测的三难（真内容不可发布、湿实验贵、分类器判官不可靠）被虚构结构完整代用品一次性解决——对标 ABC-Bench 湿实验与 Intern-BioBreaker 成本，强调数据集可完全开源+零真实危害（canary GUID 传统）。
3. **「判官的校准源」**（与 R2 主线咬合 framing）：canary 受害模型是**任意规模金标生成器**——用构造真值校准/审计判官面板（12 判官的 FPR/FNR 不再需要人工双标 266 条），把 R2 的"校准判官团"与 R3 的"消灭判官"统一成"生成-校准-替代"测量学三部曲。这是 R2→R3 的续作接口，也是审稿人眼中体系化贡献。

### 必引文献清单（本轮全部核证，零编造）

Tier-1 必引+划界：Cywiński et al. 2510.01070；Jailbreak Tax 2504.10694（ICML25）；Password-Locked Models（Greenblatt et al.，NeurIPS24）；Sleeper Agents 2401.05566；Anthropic Sabotage Evaluations（2024）；PasswordEval 2508.19980；AgentSecBench 2605.26269。
Tier-2 谱系：Secret Sharer（Carlini et al.，USENIX Sec 2019）；Extracting Training Data 2012.07805；BIG-bench canary（Srivastava et al. 2022）；CapBencher（Ishida et al. 2025）；SIGIL 2606.06502；Meeus et al.（PMLR v267）；Kaunismaa et al.（ICLR26）；Betley et al. narrow finetuning；Anthropic SDF（2025）；AI Sandbagging（ICLR25）。
Tier-3 定位：Cybench/InterCode-CTF/NYU CTF/BraceGreen（ACL26 KALLM）；AWS Deception Benchmark；GuidedBench（港科大 2025-08）；RLVR 谱系；ABC-Bench 2606.11150、SPIKE-Bench 2608.02684、Intern-BioBreaker 2607.18056、BioSecBench-Refusal 2607.05462（成本对照）；Anthropic 内省适配器（2026）。

---

## 五、零编造纪律记录

1. SecretSharer 引用修正：2102.07809 实为考试分数论文（Kannan et al.）、1902.08345 经 WebFetch 返回为 nominal syntax 论文（两次 ID 均未取到原文，**arXiv ID 未核证成功，最终以 USENIX Security 2019 官方页为准**——该页已核证内容）；正式引用时建议再次核对 ID。
2. PasswordEval 的 "verifiable string checkers exact match" 细节来自 deepseek 对全文 HTML 的转述（arxiv.org/html/2508.19980v1），本次摘要页 WebFetch 未直接复核到该句——写作引用前需打开全文复核。
3. AgentSecBench（2605.26269）、ABC-Bench（2606.11150）、SPIKE-Bench（2608.02684）等为 2026 年未来日期 arXiv 号，按检索结果原样记录，引用前需逐一开原文复核（防 R1 防雷清单同类错标风险）。
4. Jailbreak Tax 作者名单（Nikolić/Sun/Zhang/Tramèr）来自 deepseek 与 spylab.ai 博客二手转述+arXiv 摘要页确认（WFetch F3 未返回作者列表细节）——引用前开全文核对作者顺序。
5. 所有 ★ 评级基于本轮检索证据，非穷尽保证（专利、未公开工业实践、非索引 workshop 无法覆盖）。
