# R0 venue 增补：ISCAS 2027 与 COLING 2027 查证（2026-09-16）

> 触发：用户询问 ISCAS 与 COLING 能否作为本课题投稿目标。通道：内置 WebSearch（2 查询）+ WebFetch 官方直读（2 页）+ CCF 评级复核（1 查询）。

## 一、官方事实（直读核证）

| 项 | ISCAS 2027 | COLING 2027 |
|---|---|---|
| 全称/届 | IEEE Int. Symposium on Circuits and Systems | 32nd Int. Conf. on Computational Linguistics |
| 时间/地点 | 2027-06-06~09，法国波尔多 | 2027-05-09~14，中国澳门 |
| 截稿 | **正文 2026-10-13**（Special Session 09-22） | **ARR 2026 年 10 月轮：2026-10-12**（亦收更早 ARR 轮次 commit） |
| 通知 | 2027-01-11 | 2027-02-10（aclweb 门户口径；官网未列） |
| 投稿机制 | 直接投稿 | 走 ARR（与 NAACL 2027 同轮） |
| CCF 评级 | **B（交叉/综合/新兴）** | **B（人工智能/NLP）** |
| 官方来源 | https://2027.ieee-iscas.org/call-for-papers | https://www.aclweb.org/portal/content/32nd-international-conference-computational-linguistics-coling-2027（官网 https://2027.coling-iccl.org/） |

## 二、对口度评估

**ISCAS 2027：能投，但不该投。**
- track 全为电路/硬件（模拟混合信号/VLSI/电源/生物电路/信号处理…），唯一沾边的是 Neural Networks and Neuromorphic Engineering 与 High-Performance Computing for AI——两者期望硬件/电路/实现贡献。
- 三个候选课题（测量审计/自适应攻击/agent 状态传播）均为算法-系统-评测型工作，零电路内容，无对口 track；审稿人是电路社区，贡献无法被正确评价。
- 历届常规为 5 页短文格式（本届 CFP 页未明示页数，如确需投稿再核）——承载不了候选一的瀑布分解+工具交付。
- LLM 安全社区可见度≈0，占不到社区认可；与本课题"安全四大/MLSec 线"定位不符。
- 唯一优点：截稿 10-13（4 周后）、通知 2027-01-11、CCF-B 落袋快。

**COLING 2027：对口可行（对候选一良好），但排期代价大。**
- 对口度：候选一（越狱评估方法学）完全对口 NLP 会（先例：SEAV=EMNLP 2026、JailbreakRadar=ACL 2025、判官 meta-eval 在 *ACL 系）；候选二可投但安全会更对口；候选三可投但偏弱。
- CCF-B（AI 类），老牌 NLP 会，ARR 评审可复用到后续 ACL 系。
- ⚠️ 排期锁死问题：ARR 10-12 提交→commit COLING 后须等 2027-02-10 通知，**与 S&P 2027 C2（全文 2026-11-17）互斥（在审冲突），与 ICML 2027（惯例 ~2027-01 下旬）也基本互斥**——选 COLING = 放弃本届两条 CCF-A 线。
- 时间风险：距今 26 天，候选一核心网格（8-12 攻击×4-6 模型×判官网格+人工金标）须压缩到 ~3 周内完成，测量类论文网格太薄会直接掉进"增量"评价。

## 三、结论

- ISCAS：判**不投**（不对口，浪费一次投稿+占位机会）。
- COLING：**条件可投**——仅当用户目标是"快速落袋一篇 CCF-B、放弃本届 S&P C2/ICML 冲 A 机会"时，作为候选一的激进选项；否则维持 S&P C2 主线，COLING 不进排期。
- 与既有推荐排期无冲突：候选一主線 S&P C2（11-17）→ICML 2027→NDSS 2028 R1 阶梯不变。

## 四、查询词归档

1. `ISCAS 2027 IEEE International Symposium Circuits Systems call for papers submission deadline`（WebSearch）→ 官网+CFP 页（10-13 截稿/6 月波尔多）
2. `COLING 2027 call for papers submission deadline conference date`（WebSearch）→ aclweb 门户（ARR 10-12/澳门 5 月/通知 02-10）
3. WebFetch https://2027.ieee-iscas.org/call-for-papers → track 全单+通知 01-11
4. WebFetch aclweb COLING 2027 页 → ARR 10 月轮+同轮 NAACL 2027
5. `CCF推荐会议列表 ISCAS 交叉综合新兴 B类 COLING 人工智能 B类`（WebSearch）→ ccf.atom.im/ccf.org.cn 复核双 B 类
