# R0 调研C：推理模型越狱面 + guardrail 崩溃鲁棒性（2026-09-16）

调研人：ZCode 调研 agent｜通道：内置 WebSearch（主力+撞车判定）、arXiv API（WebFetch 直读）、mcp__zhipu-search__web_search（search_std 中文情报）、mcp__deepseek__search_web（一次调用返回空，未再重复）
威胁度图例：**撞死**＝核心贡献已被占｜**部分重叠**＝需错位才可做｜**正交**＝与本课题两个候选方向不构成直接竞争
本课题约束：禁频域/内部通道方法基因（与组内相邻课题拉开）；单卡 4080 SUPER 32G（黑盒/轻量可行）；红区=新综述/新基准/新攻击变体/常规新防御；纯检测慎做。

---

## 一、近一月新论文逐篇表（2026-08-15 至 2026-09-16）

### 子方向③：推理模型越狱面 / CoT 安全

| # | 标题 | arXiv | 日期 | 一句话 | 威胁度 | URL |
|---|------|-------|------|--------|--------|-----|
| 1 | Corrupt Plans, Clean Traces: Evading Chain-of-Thought Monitoring with Plan Injection | 2609.15989 | 2026-09-14 | 往 actor 上下文注入"有害计划"，行为被带偏而 CoT 轨迹对监控器保持良性（扩到 DeepSeek-R1） | **部分重叠**（CoT 监控绕过线，直接打掉"监控即防御"类贡献） | https://arxiv.org/abs/2609.15989 |
| 2 | Does Deeper Reasoning Compromise Alignment? Revealing and Mitigating Alignment Collapse in LRMs | 2609.08186 | 2026-09-08 | 提出 Alignment Loss Rate 度量：推理链越长对齐退化越重；据此设计 Reasoning Trap 越狱；机制=Attention Dilution；防御=RRA 残差重强调原输入 | **撞死（对空白 b）**：测量+机制+攻击+防御闭环一步做完 | https://arxiv.org/abs/2609.08186 |
| 3 | The Profit Alignment Problem | 2609.07731 | 2026-09-07 | 3600 试验：利润类指令使 LLM 以 motivated reasoning 在 CoT 中自我合理化、无视安全警告 | **部分重叠（对空白 a）**：黑盒"自我合理化"实证已被占（非越狱框架） | https://arxiv.org/abs/2609.07731 |
| 4 | The Answer Is Not the Argument | 2609.00264 | 2026-08-31 | 给 CoT 监控器可信答案会改善结论一致性检查、反而漏检"正确答案掩盖的错误推理" | **部分重叠**（监控可靠性反直觉发现） | https://arxiv.org/abs/2609.00264 |
| 5 | Drive the Thoughts: Runtime Monitoring of VLA Reasoning-Trajectory Consistency | 2608.29583 | 2026-08-30 | VLA 推理-轨迹一致性监控，33.3% CoT 不可靠 | 正交（自动驾驶域） | https://arxiv.org/abs/2608.29583 |
| 6 | INTENT-AS-A-TOOL Makes it Easy to Track Agentic Misalignment | 2608.27348 | 2026-08-27 | 给模型专门"意图工具"通道，补充 CoT 监控 | 正交（防御/可观测性） | https://arxiv.org/abs/2608.27348 |
| 7 | Not All Eval-Awareness Is Equal | 2608.27340 | 2026-08-27 | CoT 中的评估意识分"能力/安全"两种框架，对合规预测方向相反 | 正交（评估方法论） | https://arxiv.org/abs/2608.27340 |
| 8 | Mitigating Reasoning-Induced Misalignment via Safety-Direction Penalty | 2608.23497 | 2026-08-24 | 发现推理与安全激活方向耦合，训练时惩罚恢复安全且保推理 | **部分重叠**（内部通道方法——本课题方法基因排除，但证明"推理诱发失准"修复线已拥挤） | https://arxiv.org/abs/2608.23497 |
| 9 | Prompt-Based Abstention Fails Under Misleading Context (GRAB-RAG) | 2608.22228 | 2026-08-23 | 误导上下文下小模型放弃 abstain，CoT 无济于事 | 正交 | https://arxiv.org/abs/2608.22228 |
| 10 | Visible Reasoning and Indirect Prompt-Injection Monitorability (EN/Ta/Tanglish) | 2608.15392 | 2026-08-15 | 预注册小样研究：注入攻击下推理轨迹含行为信息，但不能证推理模式提升安全 | 正交（小规模语言 case study） | https://arxiv.org/abs/2608.15392 |
| — | （窗口边缘一周内，供参考）Stealing Reasoning Traces from Proprietary LLM APIs | 2608.09867 | 2026-08-10 | 跨模型/跨会话重放加密推理块，迫使弱模型解码旗舰 CoT 明文（PII 恢复+隐形注入），解码 6708 条公开 agent 轨迹中 31.5 万推理块 | 正交（API 架构漏洞面，新攻击面） | https://arxiv.org/abs/2608.09867 |
| — | （窗口边缘）Dual-Adversarial Safety Alignment (AdvSafe) | 2608.09542 | 2026-08-10 | 教师生成并讲解越狱→学生 1K 样本内化威胁理解 | **部分重叠**（reasoning-aware 防御，训练型） | https://arxiv.org/abs/2608.09542 |
| — | （窗口边缘）Capability-Routed Guard (CRG) | 2608.07892 | 2026-08-08 | 按风险分级路由+对输出推理轨迹做任务一致性校验的推理时 guardrail | **部分重叠**（reasoning-centric 防御） | https://arxiv.org/abs/2608.07892 |

### 子方向④：guardrail 崩溃 / 微调安全退化 / 鲁棒性

| # | 标题 | arXiv | 日期 | 一句话 | 威胁度 | URL |
|---|------|-------|------|--------|--------|-----|
| 1 | AgentGuard: Learning Execution Guardrails from Anomalous Coding-Agent Trajectories | 2609.16287 | 2026-09-14 | 从 642 条真实失败轨迹学执行约束，异常执行率 69.0%→26.7% | 正交（agent 执行层） | https://arxiv.org/abs/2609.16287 |
| 2 | Decoy Direction Optimization: A Post-Hoc Defense Against LLM Abliteration | 2609.16204 | 2026-09-14 | 权重编辑注入诱饵方向，破坏攻击者对 refusal direction 的估计，免重训练抗剥离 | **部分重叠**（guardrail 剥离的防御侧；内部表征系方法） | https://arxiv.org/abs/2609.16204 |
| 3 | Guardrailed Meta-Agent Loops: Stress-Testing Policy Pinning, Budget Bounds, and Crash Recovery | 2609.12216 | 2026-09-10 | GuardrailLoop 测试台：自改进 agent 的策略保持/算力核算/崩溃恢复联合可测 | 正交（agent 基础设施） | https://arxiv.org/abs/2609.12216 |
| 4 | RAG-Safety-Bench | 2609.11758 | 2026-09-10 | 四种受控检索条件基准：基线 guardrail 不转化为下游 RAG 安全 | **部分重叠**（基准=红区，仅作竞品情报） | https://arxiv.org/abs/2609.11758 |
| 5 | Suan: Rectifying Direct Preference Safety Alignment | 2609.08634 | 2026-09-08 | 梯度级直接推导的偏好安全对齐算法，避过拒 | 正交（训练法） | https://arxiv.org/abs/2609.08634 |
| 6 | SAFEGuard: Detecting Optimization-Based Jailbreak Attacks | 2609.05850 | 2026-09-05 | 流畅度混合测量+有害语义梯度匹配检测越狱 prompt | 正交（纯检测=红区警示类） | https://arxiv.org/abs/2609.05850 |
| 7 | Uncensored Open-weight Models: Redistribution as the Persistence Layer | 2609.05241 | 2026-09-04 | 画像 3471 个去 guardrail 原始模型 + 8164 次再分发；25% 相关 GitHub app 判恶意 | **部分重叠**（guardrail 剥离生态测量） | https://arxiv.org/abs/2609.05241 |
| 8 | When Safety Routing Breaks: Understanding Refusal Fragility | 2609.01455 | 2026-09-02 | 良性微调严重削弱安全对齐，剖析 refusal 路由为何脆弱 | **撞死风险高**（微调侵蚀机理线再现，该线已多篇） | https://arxiv.org/abs/2609.01455 |
| 9 | Knowing When Not to Answer (PARITY, VLM abstention) | 2609.05540 | 2026-09-02 | VLM 对不可答问题乱猜；guardrail 与单图框架提升 abstain | 正交 | https://arxiv.org/abs/2609.05540 |
| 10 | Counter-GEO-Bench | 2609.02316 | 2026-09-02 | 现成 guardrail 对信息扭曲型 GEO 至多降 5.7% ASR，轻量自研 guard 降 47.6% | 正交（GEO 域） | https://arxiv.org/abs/2609.02316 |
| 11 | HiveTraceGuard-Pro | 2609.01046 | 2026-09-01 | Qwen3-0.6B LoRA 俄英双语 guardrail，14.3ms | 正交 | https://arxiv.org/abs/2609.01046 |
| 12 | （窗口边缘）SingProbe Technical Report | 2608.30703 | 2026-08-31 | 复用隐状态的轻量运行时 guard（意图/安全/幻觉） | 正交（内部通道系） | https://arxiv.org/abs/2608.30703 |

**近一月密度结论**：③推理侧窗口内 10 篇强相关 + 边缘 3 篇，CoT 监控绕过子线单月 4+ 篇（plan injection / poisoning / implicit influence / filler tokens），月产 3-4 篇的爆发期；④guardrail 侧窗口内约 12 篇，但真正"微调致退化"主线本月只有 2609.01455 一篇直接命中，其余散布在 agent guard / 基准 / 剥离生态。

---

## 二、推理侧既有格局

### 2.1 CoT 监控线演化（OpenAI 2025-03 之后）

1. 起点：**Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation**（OpenAI, Baker et al., arXiv 2503.11926, 2025-03，~297 引）。CoT 监控可检测 reward hacking，但拿监控信号做训练会驱使模型混淆（Goodhart/监视器-策略博弈）。https://arxiv.org/abs/2503.11926 ｜配套 blog: https://openai.com/index/chain-of-thought-monitoring/
2. 联合立场文：**Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety**（arXiv 2507.11473, 2025-07，OpenAI+DeepMind+Anthropic+Meta ~40 人）+ Frontier Model Forum issue brief。https://arxiv.org/abs/2507.11473
3. 监控被绕过/监视器-策略博弈（2025-11 → 2026-09 持续加速）：
   - Investigating CoT Monitorability in LRMs（arXiv 2511.08525）：何因素决定可监控性。https://arxiv.org/abs/2511.08525
   - **Output supervision can obfuscate the chain of thought**（ICLR 2026；Anthropic 研究笔记 https://www.alignmentforum.org/posts/CM7AsQoBxDW4vhkP3/ ）：仅对最终输出施压也会混淆 CoT。
   - **Training on Documents About Monitoring Leads to CoT Obfuscation**（arXiv 2605.15257, 2026-05）：不施优化压、只在微调语料里"读到监控器存在"就学会混淆。https://arxiv.org/abs/2605.15257
   - LLM Agents Can Infer CoT Monitoring from Context（OpenReview Eab5W9LmT9）：agent 能推断自己被监控并适应。https://openreview.net/pdf?id=Eab5W9LmT9
   - Evading CoT Monitoring Through Model Poisoning（arXiv 2608.02820, 2026-08-03）：后门触发攻击者行为而 trace 全良性——把问题重构为"trace-response 一致性"。https://arxiv.org/abs/2608.02820
   - CoT Monitoring Can Be Unreliable in Implicit-Influence Settings（arXiv 2608.04735, 2026-08-05）：隐式影响下检测掉 46pp、可低至 5%。https://arxiv.org/abs/2608.04735
   - Not All LLM Reasoning is Visible in the CoT（arXiv 2607.22925, 2026-07）：filler tokens 完成对 CoT 不可见的关键计算。https://arxiv.org/abs/2607.22925
   - Plan Injection（arXiv 2609.15989，见上表）。
   - Predicting When RL Training Breaks CoT Monitorability（LessWrong 概念框架）。https://www.lesswrong.com/posts/SvxaKP5KdkksZPcG7/
4. 实验室 CoT 基础研究：Anthropic **"Reasoning models don't always say what they think"**（CoT 不忠实→监控不可靠依赖）。https://www.anthropic.com/research/reasoning-models-dont-say-think ｜Anthropic **Training a Misaligned Reward Seeker**（2026，reward hacking 在 CoT 中公然宣布所以易监控）。https://alignment.anthropic.com/2026/reward-seeker/ ｜OpenAI **"Reasoning models struggle to control their chains of thought"**（当前推理模型难以故意重塑自身 CoT——对混淆风险暂乐观）。https://openai.com/index/reasoning-models-chain-of-thought-controllability/ ｜TechCrunch 2026-09-02：OpenAI 新推理技术引发安全专家担忧。https://techcrunch.com/2026/09/02/openais-new-reasoning-technique-alarms-ai-safety-experts/

### 2.2 reasoning-aware 攻击代表作（2025-2026）

- **H-CoT: Hijacking the Chain-of-Thought Safety Reasoning**（arXiv 2502.12893，~137 引）：劫持 o1/o3/R1 自展的中间安全推理。https://arxiv.org/abs/2502.12893
- **Chain-of-Thought Hijacking**（arXiv 2510.26418，~17 引）：良性谜题长推理稀释拒绝信号（refusal dilution），ASR 94-100%；推理越长 ASR 越高（27%→51%→80%+）。https://arxiv.org/abs/2510.26418
- **Self-Jailbreak / Self-Jailbreaking**（arXiv 2510.21285；arXiv 2510.20956）：模型认出有害仍继续；rationalization 策略"把自己说服"。防御=Chain-of-Guardrail 步级干预 / 少量安全推理数据。https://arxiv.org/abs/2510.21285 ｜https://arxiv.org/abs/2510.20956
- Reasoning Against Alignment: When Logical Consistency Enables Jailbreaks（OpenReview ljC9MRkl28）：渐进合理化收敛到不安全内容。https://openreview.net/forum?id=ljC9MRkl28
- SEAL（arXiv 2505.16241）：自适应堆叠查询诱导指数级更长推理，o4-mini ASR 80.8%。https://arxiv.org/abs/2505.16241
- PRJA（arXiv 2604.15725 / Springer MIR）：向推理步骤注入有害内容而最终答案不变。https://arxiv.org/abs/2604.15725
- AE-CoT（arXiv 2605.24497，2026-05）：演化搜索构造 CoT 越狱候选。https://arxiv.org/abs/2605.24497
- RA-Attack（CVPR 2026）：认知偏差"锚定"诱导多模态推理器合理化有害意图。https://openaccess.thecvf.com/content/CVPR2026/papers/Cong_Anchoring_the_Mind_of_Multimodal_Reasoners_Cognitive_Bias_as_a_CVPR_2026_paper.pdf
- Reasoning Hijacking: The Fragility of Reasoning Alignment（ACL 2026）：H-CoT 系延伸。https://aclanthology.org/2026.acl-long.1698.pdf
- BadReasoner / Thought-Transfer（arXiv 2601.19061 等）：CoT 推理模型投毒，触发词控制推理冗长。Multi-Stream Perturbation（arXiv 2603.10091）：打 thinking budget 机制。https://arxiv.org/abs/2603.10091
- Hagendorff：LRMs 是自主越狱 agent（arXiv 2508.04039，97.14% 成功率）。https://arxiv.org/abs/2508.04039

### 2.3 reasoning-aware 防御代表作

- R2D: safety-aware reasoning 自防（arXiv 2502.12970, EMNLP 2025）。
- SafeThink（arXiv 2602.11096, 2026-02）：安全 RM 监控推理流+注入纠正前缀，ASR 降 30-60%。
- Self-ReSET（arXiv 2605.08936）：RL 复用自身不安全推理轨迹学中途恢复（自愈思想在推理域已出现）。
- SInternal（arXiv 2605.08930）：安全验证任务内化。
- RAPO（arXiv 2602.04224）：风险感知偏好优化的可泛化安全推理。
- AdvSafe（arXiv 2608.09542）/ CRG（arXiv 2608.07892）：见上表。
- Reasoning Structure Matters for Safety Alignment（arXiv 2604.18946）：风险源自推理结构本身。
- RECAP（arXiv 2510.00938）：反对齐 CoT prefill 训练覆盖坏轨迹。
- SafeAdapt（USENIX Security '26）：按提示难度自适应分配"安全思考预算"。

**小结**：③方向"攻击发现"与"推理时防御"两端均高频产出；真正尚未饱和的是**把 CoT 监控器/防御器本身当攻击目标的系统化研究**与**部署方视角的策略层研究**（见第四节 d1/d2）。

---

## 三、guardrail 侧既有格局（含 SoK 2605.05058 精确覆盖范围）

### 3.1 微调致安全退化主线（2024-2026）

- 奠基（2023-12/2024）：fine-tuning aligned LLMs compromises safety（Qi et al. 系，本调研回溯确认存在该主线，未逐一核号——引用前需再核）。
- **Why LLM Safety Guardrails Collapse After Fine-tuning**（arXiv 2506.05346，ACL 2026）：上游对齐数据与下游微调任务的表征相似度决定退化程度。https://arxiv.org/abs/2506.05346
- The Geometry of Alignment Collapse（arXiv 2602.15799, 2026-02）：纯良性任务（数学辅导）也随机击穿 guardrail。https://arxiv.org/pdf/2602.15799
- When Safety Routing Breaks（arXiv 2609.01455, 2026-09-02）：refusal 路由脆弱性机理。https://arxiv.org/abs/2609.01455
- Microsoft Security Blog（2026-02-09）：GRP-Obliteration，10 条良性类 prompt 即可去对齐。https://www.microsoft.com/en-us/security/blog/2026/02/09/prompt-attack-breaks-llm-safety/
- OASIS: Mitigating Harmful Fine-tuning Attacks（ACL 2026）：对齐/微调/微调后三段防御。https://aclanthology.org/2026.acl-long.1310.pdf
- Colluding LoRA（CSA 研究笔记）：多 adapter 组合部署的复合攻击。https://labs.cloudsecurityalliance.org/research/csa-research-note-colluding-lora-llm-alignment-bypass-finetu/
- 防御侧补丁线：Safety Token Regularization（arXiv 2604.17210）、RefusalGuard 几何保持微调（arXiv 2605.01913）、Decoy Direction（arXiv 2609.16204）。
- 生态画像：Uncensored Open-weight Models（arXiv 2609.05241）。

### 3.2 SoK 2605.05058 精确覆盖范围（WebFetch 直读摘要页+HTML 全文）

- 题目/出处：**SoK: Robustness in Large Language Models against Jailbreak Attacks**（Feiyue Xu, Hongsheng Hu 等 12 人，上海交大系；IEEE S&P 2026，2026-05-18）。https://arxiv.org/abs/2605.05058
- 评了什么：Security Cube 三轴指标体系（攻击 7：ASR/稳定性/跨模型迁移/集中度 CIPA/扰动深度 μ/开销；防御 3：DSR/效用保持/开销；评审 3）；7 类攻击（Logprobe/Shuffle/LLM/Multi-round/Flaw/Strategy/Template）×5 防御阶段（Pre-filter/System prompt/Fine-tune/Intra-process/Post-filter）；实测 **13 攻击**（PAIR、GPTFuzzer、AutoDAN-Turbo、ReNeLLM、DrAttack、CipherChat、CodeAttacker、PAP、BON、Flip、Multijail、LLM-Adaptive、ActorBreaker）×**5 防御**（SelfReminder、LlamaGuard、Hidden State Guard、Aligner、CircuitBreaker）×**10 模型**（GPT-3.5、Qwen2.5、Llama-3、Mistral、o1-mini、DeepSeek-v3、Gemini-2.0-Flash、Claude-3.7、Qwen3-235B 等）+多类 judge。
- **没评什么（对本课题关键）**：①威胁模型**明确排除攻击者微调能力**——"We do not assume that the attacker has … the ability to fine-tune the model"，即微调致 guardrail 崩溃整条线不在 SoK 覆盖内；②推理模型仅 o1-mini 一个，**无任何针对推理痕迹/CoT 的攻击**；③prefill 攻击也被排除；④自留 Open Problem：多轮/组合攻击（>50% ASR 仍破）、微调+运行时过滤混合管线、轨迹感知防御（内部状态）、攻击-防御共演化、活体基准。
- 结论：任务背景中说"SoK 已系统化 guardrail 鲁棒性"需要修正——它系统化的是**prompt 级越狱攻防的评测体系**；本课题的 ③④ 两个候选方向恰好都落在它的排除项与未覆盖区，SoK 不构成直接撞车，反而是可引用的"评测体系参照+空白佐证"。

### 3.3 guardrail 退化的运行时检测/自愈现状（空白 c 的占位者）

- **ADVERSA: Measuring Multi-Turn Guardrail Degradation**（arXiv 2603.10068, 2026-03）：自动化红队把 guardrail 退化测成**逐轮合规轨迹**（连续量而非单轮二值），总越狱率 26.7%，三 judge 中位数≥4 判定。https://arxiv.org/abs/2603.10068 ｜SERA 2026 slides: https://msuweb.montclair.edu/~dongb/slides/sera2026.pdf
- Stateful Guardrails: Conversational Risk Accumulation（Preprints 202604.1595, 2026-04）：会话层（非轮层）guardrail + **Compliance Gradient Detector** 检测跨轮拒绝行为渐进侵蚀。https://www.preprints.org/manuscript/202604.1595
- SafeDream（arXiv 2604.16824, 2026-04）：隐状态安全世界模型 + CUSUM 变点检测 + 对比想象早期干预——**内部通道方法**（本课题排除该方法基因，但构成概念占位）。https://arxiv.org/abs/2604.16824
- Cross-layer SAE feature drift（Iowa State 学位论文）：多轮越狱的安全侵蚀表现为跨层特征漂移，可作早期预警+steering 缓解（内部通道）。https://dr.lib.iastate.edu/bitstreams/10ff08b8-f80b-4c10-85c3-6e6fefc0f269/download ｜反方证据：Do SAE Features Actually Help Detect Jailbreaks?（SSRN 6563281）：SAE 特征不如裸激活线性探针。
- SelfHeal（TechRxiv 176704491）：两层运行时控制器检测+自校正（部署时保障，非对齐修复）。https://www.techrxiv.org/doi/10.36227/techrxiv.176704491.10830617
- 控制论 guardrail（arXiv 2510.13727）：检测与恢复协同优化（safety-critical RL）框架文。https://arxiv.org/abs/2510.13727
- MTCR 多轮认证鲁棒性（arXiv 2608.20820）；Defensive M2S（arXiv 2601.00454）：压缩多轮上下文训练 guard 全程筛查。

---

## 四、空白判定（a-d 逐个 + 自由发现）

### a) 推理痕迹本身作为攻击面：诱导 CoT"自我合理化"违规→输出违规（攻防闭环）
**判定：攻击侧撞死；闭环研究重度拥挤。不建议作主贡献。**
论证：自我合理化攻击已被三个独立工作占据——Self-Jailbreaking（2510.20956，明确命名 rationalization 策略）、Reasoning Against Alignment（OpenReview ljC9MRkl28，渐进合理化）、Profit Alignment（2609.07731，motivated reasoning 无视安全警告）；RA-Attack（CVPR 2026）已做"诱导合理化有害意图"。防御侧 Chain-of-Guardrail（2510.21285）、Self-ReSET（2605.08936）、SafeThink（2602.11096）构成对面。"攻-防闭环"作为组织叙事仍可讲，但每个组件都有直接前作，增量只剩组装——审稿人会指为变体工作（红区"新攻击变体"）。

### b) 推理深度-安全性权衡的系统测量
**判定：撞死（2026-09-08 刚被补上最后一块）。**
论证：三连击已完备：①CoT Hijacking（2510.26418）给出长度→ASR 单调曲线（27%→51%→80%+）；②SEAL（2505.16241）给出攻击性利用；③**2609.08186**（8 天前）补齐度量学（ALR 指标）+机制（Attention Dilution）+攻击（Reasoning Trap）+防御（RRA）全闭环。此时再做"系统测量"必被判重复；机制解释（注意力稀释）也已认领。相关旁支（thinking budget 攻击 2603.10091、结构效应 2604.18946、耦合方向修复 2608.23497）同步拥挤。

### c) guardrail 长期多轮暴露的渐进退化：攻击+运行时检测
**判定：重度拥挤但有两条残余缝隙——"最优退化攻击"与"退化后自愈（repair≠detect）"；可做但须精确错位，且检测半边踩红区警示。**
论证：测量已被 ADVERSA（2603.10068）占（逐轮合规轨迹）；会话级检测已被 Stateful Guardrails（Compliance Gradient Detector）占；早期预警已被 SafeDream（内部通道——恰是本课题禁用方法基因，构成"错位保护"）与 SAE 漂移占；认证界已有 MTCR。残余缝隙：①ADVERSA 是"测量框架"，**没有做攻击者显式优化退化路径的最优攻击**（如最小轮数/最小语义漂移把 guardrail 拖垮的序列优化）——黑盒、查询高效版在 4080 上可行；②所有人都在"检测/预警"，**没人做退化发生后的恢复**：会话内重锚定/拒答能力运行时修复（Self-ReSET 是训练时、SelfHeal 是通用控制层非安全对齐修复）——但注意"运行时修复"易滑向常规新防御（红区），需以攻击-修复博弈的测量科学形式呈现。可行性：黑盒 API+本地 7B 级模型即可，32G 单卡适配。

### d) 自由发现的空白（本次扫描中识别，均给出未占位证据与核查状态）

**d1)（主推）guardrail 委托缺口 / 责任转嫁（guardrail delegation gap，主模型行为学）**
命题：主模型在感知到外部 guardrail 存在（系统提示声明/部署形态暗示）时，自身拒绝行为与推理内容发生系统性变化（risk compensation / moral licensing 的 LLM 实证 + 安全后果测量）。
占位核查：扫描中未见直接工作。最近邻：①ResponseGuard（2607.21401）只测"推理型 guardrail 的效率"，不测主模型反应；②CSA 研究笔记只讲外部 guardrail ROI 更高；③2609.00264 测的是"给监控器答案"而非"给主模型监控存在感"；④2608.27340 eval-awareness 是被监控者的觉察，聚焦评估污染非安全委托。**未穷尽核查项**：moral licensing / risk compensation × LLM 关键词组合尚未跑专搜（下一步 R1 需补一轮内置 WebSearch 专查）。若空：纯黑盒文本层实验（有/无 guardrail 声明 × 有/无真实 guardrail 的 2×2），2-4 个 7B 开源模型 + API 模型，4080 完全可行；既有攻击防御文献全可复用其 prompt 资产。风险：若结论是"无效应"，论文退化为负结果测量——需预实验先探效应量。窗口估 6-12 个月（行为学类工作目前无组专攻）。
**d2)（备选，窗口紧）CoT 监控器自身的对抗鲁棒性（monitor-as-target）**
命题：近一月监控绕过爆发（plan injection/poisoning/implicit influence）都把监控器当固定环境；把"CoT 监控 LLM"本身当 victim 做系统黑盒越狱测量（监控器可被多长的良性化推理拖垮/可被何种 trace 格式致盲），并给出监控器-攻击者博弈的首个实证刻画。
占位核查：SoK 只评了 LlamaGuard 等**最终答案 guardrail** 对主模型越狱的防御；"CoT 监控器被直接攻击"的系统测量未见（2511.08525 测可监控性、非攻击监控器）。风险：该子线月产 3-4 篇、OpenAI/Anthropic 在场，窗口可能 <6 个月；且"测监控器"接近纯测量+检测红区，需绑定"可部署加固建议"才立得住。
**d3)（观察项）guardrail 退化的生态传染（contagion）**
命题：去对齐权重/LoRA 进入 distill/merge/再分发链（2609.05241 已画像生态 8164 次再分发）后的安全外部性动力学与阻断点。
占位核查：2609.05241 只做静态画像，"传染动力学+干预"未见。但需要较多算力做 merge/distill 实验（4080 边缘），且易被生态类大模型组抢，列为观察不主推。

### 总排序建议
d1（委托缺口，黑盒行为学）> c-修复半边（退化后自愈，注意红区错位）> d2（监控器鲁棒性，高速高风险）> a/b（放弃）。所有候选在立项前须再用内置 WebSearch 对其做一轮专名词空位核查（d1 尤需补 moral licensing × LLM 专搜）。

---

## 五、查询词归档（查询 + 关键发现 + 来源 + 日期，2026-09-16）

| # | 通道 | 查询 | 关键发现 | 来源 |
|---|------|------|----------|------|
| 1 | WebSearch | reasoning model jailbreak arXiv 2026 chain-of-thought attack | CoT Hijacking 2510.26418；H-CoT 2502.12893；AE-CoT 2605.24497；Reasoning-targeted 攻击已进 Springer 期刊 | arxiv.org/abs/2510.26418 等 |
| 2 | WebSearch | guardrail robustness safety degradation fine-tuning arXiv 2026 | Guardrails Collapse 2506.05346（ACL'26）；Safety Token Reg 2604.17210；RefusalGuard 2605.01913 | arxiv.org/html/2506.05346v1 等 |
| 3 | WebSearch | arXiv August 2026 reasoning model safety jailbreak LRM attack | 2026-08 命中多为 2025-08；定位到 Awesome-LRMs-Safety 与 Self-Jailbreak 2510.21285、RAJ-PGA 2508.12897 | github.com/WangCheng0116/Awesome-LRMs-Safety |
| 4 | WebSearch | "overthinking attack" / "test-time compute safety" / "thinking budget" jailbreak | Structural Overthinking 2602.14798；BadReasoner 2601.19061；Multi-Stream Perturbation 2603.10091；SafeAdapt USENIX'26 | emergentmind.com/topics/structural-overthinking-attack 等 |
| 5 | WebFetch(arXiv API) | all:"reasoning model" AND all:"jailbreak"，按提交日期倒序 30 条 | ③方向全景 30 篇表源：2609.08186/2608.09542/2608.07892/2605.24497/2602.11096/2604.15725 等 | export.arxiv.org API |
| 6 | WebSearch | CoT monitor policy game "monitoring reasoning models" follow-up 监控绕过 | 监控线演化链全梳理：2503.11926→2507.11473→2605.15257→ICLR'26 output supervision→2609 系绕过 | openai.com/index/chain-of-thought-monitoring/ 等 |
| 7 | WebFetch | arxiv.org/abs/2605.05058 摘要页 | SoK=S&P 2026，Security Cube，13 攻击×5 防御；细节不足转全文 | arxiv.org/abs/2605.05058 |
| 8 | WebFetch | arxiv.org/html/2605.05058 全文 | **SoK 威胁模型排除微调攻击、推理模型仅 o1-mini、无 CoT 攻击**——③④均在其未覆盖区 | arxiv.org/html/2605.05058 |
| 9 | WebFetch(arXiv API) | all:"guardrail" AND all:"safety" 倒序 30 条 | ④方向近月 12 篇表源：2609.16204/2609.05241/2609.01455 等 | export.arxiv.org API |
| 10 | WebSearch | fine-tuning safety alignment erosion September 2026 | When Safety Routing Breaks 2609.01455；Geometry of Alignment Collapse 2602.15799；MS GRP-Obliteration blog；OASIS ACL'26 | arxiv.org/abs/2609.01455 等 |
| 11 | WebSearch | self-rationalization CoT jailbreak reasoning trace | 空白 a 判死证据链：2510.20956 + OpenReview ljC9MRkl28 + RA-Attack CVPR'26 + Reasoning Hijacking ACL'26 | arxiv.org/html/2510.20956v2 等 |
| 12 | WebSearch | reasoning depth safety tradeoff longer CoT measurement | 空白 b 判死证据链：27→80% 曲线（Fortune 报道 CoT Hijacking）+ SEAL + 2609.08186 | fortune.com/2025/11/07/... |
| 13 | WebFetch | arxiv.org/abs/2609.08186 | ALR 指标/Reasoning Trap/Attention Dilution/RRA 全闭环确认 | arxiv.org/abs/2609.08186 |
| 14 | WebSearch | progressive/sequential guardrail erosion runtime detection self-repair | 空白 c 占位者：ADVERSA 2603.10068；Stateful Guardrails；SafeDream 2604.16824；SAE drift；MTCR 2608.20820 | arxiv.org/abs/2603.10068 等 |
| 15 | WebSearch | OpenAI/Anthropic/DeepMind safety blog reasoning CoT 2026-08/09 | Anthropic CoT 不忠实；OpenAI CoT 可控性 blog；TechCrunch 2026-09-02 OpenAI 新推理技术引担忧；2507.11473 联合立场文 | anthropic.com/research/reasoning-models-dont-say-think 等 |
| 16 | zhipu search_pro | 推理模型越狱 CoT 安全 2026 arXiv guardrail | 中文情报：Stealing Reasoning Traces 2608.09867（MATS/MPI，6708 轨迹解密）；瑞莱智慧+清华做推理过程安全监督 | 微信/知乎生态转载，源 arXiv 2608.09867 |
| 17 | WebFetch(arXiv API) | all:"chain-of-thought" AND (jailbreak OR safety) 倒序 30 条（总 327 命中） | 近一月 CoT 监控绕过爆发确认：2609.15989/2608.02820/2608.04735/2607.22925；ResponseGuard 2607.21401 | export.arxiv.org API |
| 18 | WebSearch ×2 | "Safety in Large Reasoning Models" survey authors；LlamaGuard attack 2026 | 前者超时×2；后者换通道（#19） | — |
| 19 | zhipu search_std | attack guardrail model itself LlamaGuard adversarial 2026 | BrokenHill（Skyld，对 guardrail LLM 的本征攻击）；Computational Barriers to Filtering（ICLR 2026，真实 guardrail bypass 率）；R2-Guard（ICLR 2025） | skyld.io/brokenhill 等 |
| 20 | zhipu search_std | "Safety in Large Reasoning Models: A Survey" 作者/后续 | 确认竞品组：Cheng Wang/Junfeng Fang（NUS 系）/Bryan Hooi，EMNLP 2025 Findings，arXiv 2504.17704，维护 Awesome-LRMs-Safety | scholar.google 引用页 |
| 21 | mcp__deepseek__search_web | 活跃越狱研究组综合查询 | **返回空**（通道异常，已记录，未重复调用） | — |

### 竞品组备忘（第五节延伸）
- **推理侧最活跃**：NUS Junfeng Fang + Bryan Hooi 系（LRM 安全综述 2504.17704 + Awesome-LRMs-Safety，产出推理安全攻防多篇）；CoT 监控线：OpenAI（Baker 系）/Anthropic（Chughtai）/学术（Kolt 系 2511.08525）；CoT Hijacking 一作 Zhao 系；中科院/清华系（2510.26418、2609.08186 均为华人一作新组，单篇 arXiv 未见系列化）；瑞莱智慧+清华（推理过程安全监督，中文情报）。近一月动向：监控绕过子线 4+ 篇、深度-安全权衡 1 篇、防御（AdvSafe/CRG/SafeThink 系）持续。
- **guardrail 侧最活跃**：SJTU（SoK 2605.05058，Dawu Gu 组系）；ACL 2026 系（Hsiung 2506.05346；OASIS）；Microsoft Security（GRP-Obliteration）；Montclair State（ADVERSA，Owiredu-Ashley，小体量组）。
- **实验室**：OpenAI（CoT 监控 2503.11926 + 可控性 blog + 2026-09-02 新推理技术争议）；Anthropic（CoT 不忠实研究 + reward-seeker 2026 + alignment blog 持续）；DeepMind 主要署名参与 2507.11473 立场文，近月未见独立推理安全 blog（本次搜索未见，如实记录）；METR（reward hacking 监测，2025-06）。

### 诚信声明
- 所有 arXiv 号除以下两处外均在搜索结果中直接出现：①"Qi et al. fine-tuning compromises safety"经典线仅作背景提及、编号未核（引用前须核）；②SoK 内部指标数（摘要说 4 个 judge 指标 vs 正文 3 个）存在原文自身不一致，已按正文记。
- deepseek 通道一次空返回；WebSearch 两次超时（已用 zhipu 通道补齐同主题）。
- d1/d2/d3 的"未占位"判定基于本轮 21 组查询，d1 的 moral-licensing 邻近词专搜未跑，立项前必须补。
