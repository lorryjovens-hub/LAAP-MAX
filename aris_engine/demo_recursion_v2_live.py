"""现场试跑：深度递归 v2 完整流程 —— 「先验层的软化机制」两难问题。"""
import sys
sys.path.insert(0, r"D:\LAAP\aris_engine")

from recursion_engine_v2 import get_deep_recursion_engine

eng = get_deep_recursion_engine()

t = eng.open_tree(
    "先验层的软化机制如何设计：先验靠默认信任才有效，OOD 适应又要求撤销信任？"
)
root = next(iter(t.nodes))

# ── 第 1 层：why — 现象层 ──
n1 = eng.add_node(t.id, root, "why",
    "为什么先验会阻塞 OOD 发现？",
    "先验是『默认成立』的假设。环境规则违反先验时，违反事件被标记为异常，"
    "系统倾向先怀疑自己的感知，而不是接受环境规则。先验刚性越强，"
    "真规则越容易被当噪声丢弃。", "symptom")

# ── 第 2 层：counterfactual — 机制层 ──
n2 = eng.add_node(t.id, n1.id, "counterfactual",
    "如果先验完全没有默认权重（随时可推翻），会怎样？",
    "退化为无先验状态：每条规则从零验证，回到统计拟合的 O(n) 低效。"
    "先验的价值恰恰来自默认信任；信任被取消，价值同时消失。", "mechanism")

# ── 第 3 层：falsify — 原理层 ──
n3 = eng.add_node(t.id, n2.id, "falsify",
    "什么情况下『默认信任 + 证据推翻』架构会失败？",
    "反例：环境以低概率系统性违反先验（99% 时间守物理，1% 允许瞬移且瞬移是"
    "通关关键）。explanation_demand 会把低频关键事件当噪声丢弃，"
    "系统永远学不会瞬移规则。这是『罕见但关键的反常』。", "principle")

# ── 第 4 层：assume — 公理层 ──
n4 = eng.add_node(t.id, n3.id, "assume",
    "『证据推翻』范式依赖什么隐藏前提？",
    "隐藏前提是证据频率假设：推翻机制的有效性绑定于证据出现频率。"
    "但 OOD 环境可以操纵这个频率——关键证据出现太少，统计积累永远达不到"
    "推翻阈值。推翻机制的失败模式不是『太相信先验』，而是『假设了证据频率』。",
    "axiom")

# ── 第 5 层：abstract — 提取可迁移模式 ──
n5 = eng.add_node(t.id, n4.id, "abstract",
    "这蕴含什么可迁移的抽象模式？",
    "任何依赖统计证据积累的修正机制，在证据频率可被环境操纵时失效。"
    "频率不是可靠信号——这指向对抗性环境假设。", "axiom",
    pattern="统计证据积累的修正机制在对抗性/频率可操纵环境下失效")

# ── 第 6 层：analogize — 同构迁移：免疫系统 ──
n6 = eng.add_node(t.id, n5.id, "analogize",
    "别的领域哪里有同样结构？",
    "免疫系统面对『罕见但致命』的病原体时不靠统计积累（等抗体浓度够就晚了），"
    "而是靠先天免疫的 danger theory：按『危险度』而非『概率』排序响应。"
    "感染初期的损伤信号会放大响应，不需要等到证据累积。", "transfer")

# ── 第 7 层：why — 免疫系统为什么用危险度不用概率 ──
n7 = eng.add_node(t.id, n6.id, "why",
    "免疫系统为什么用危险度排序，而不是概率排序？",
    "因为免疫系统面对的是对手：病原体会主动隐藏、操纵频率信号。"
    "对抗性环境下频率不可靠，危险度（潜在不可逆损害）才可靠。"
    "OOD 任务设计虽非恶意，但刻意让频率信号失效——等价于对抗。",
    "principle")

# ── 本源三检验：第一次 —— 无替代未过（存在竞争本源） ──
eng.verify_bedrock(t.id,
    "先验软化机制的根本原则：在对抗性（频率不可靠）环境下，"
    "修正优先级应由异常的信息价值/潜在收益驱动，而非证据积累量驱动。",
    minimality=True, generativity=True, uniqueness=False,
    notes=["竞争本源：分层先验说（刚性核心+弹性外围）——但检查后发现"
           "它本质是本结论的一种实现方式，非同等底层"])

# ── 抽象跃迁：模式迁移到 LAAP 自己的问题域 ──
eng.leap(t.id, "对抗性环境下频率不是可靠信号，信息价值才是",
         [n5.id, n6.id, n7.id],
         migrated_problems=["RSI 改进评估（低频反馈下的改进判定）",
                            "记忆验证 gate（低频冲突下的阈值）",
                            "LAAP 安全监控的未知未知检测"],
         new_questions=["RSI 在低频反馈下是否也该用信息价值而非频率判定改进？",
                        "记忆 verify gate 在罕见冲突下是否误杀正确记忆？"])

# ── 补检：吸收竞争本源后第二次检验 ──
eng.verify_bedrock(t.id,
    "先验软化机制的根本原则：在对抗性（频率不可靠）环境下，"
    "修正优先级应由异常的信息价值/潜在收益驱动，而非证据积累量驱动；"
    "分层先验是这一原则的一种实现形式。",
    minimality=True, generativity=True, uniqueness=True,
    notes=["竞争本源『分层先验』已被吸收为结论的实例化，非同等底层替代"])

print(eng.report(t.id))
