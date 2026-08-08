"""
PsiLang 契约层 Step 1 验收测试
================================
验证 P1 验证通道（E7xxx 系列）的全部检查项。

运行: python tests/test_contract_step1.py

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexer import PsiLangLexer
from parser import PsiLangParser
from checker import check_program

PASS = 0
FAIL = 0


def check_source(source: str, expect_codes, label: str):
    """解析 + 检查，断言期望的错误码集合"""
    global PASS, FAIL
    try:
        tokens = PsiLangLexer(source, "<test>").tokenize()
        prog = PsiLangParser(tokens, "<test>").parse(require_creator=False)
        collector = check_program(prog, "<test>")
        got = {d.code for d in collector.diagnostics if d.severity == "error"}
        # 期望码必须是 got 的子集（允许附加错误，但关键码必须出现）
        missing = set(expect_codes) - got
        if missing:
            FAIL += 1
            print(f"[FAIL] {label}: 缺少错误码 {missing}, 实际 {got}")
            for d in collector.diagnostics:
                if d.severity == "error":
                    print(f"        {d.code}: {d.message}")
        else:
            PASS += 1
            print(f"[PASS] {label}: 命中 {sorted(expect_codes)}")
    except Exception as e:
        FAIL += 1
        print(f"[FAIL] {label}: 异常 {type(e).__name__}: {e}")


# ══════════════════════════════════════════════════════════
# 用例
# ══════════════════════════════════════════════════════════

print("=== PsiLang 契约层 Step 1 验收测试 ===\n")

# 1. 合法的 fact（全部通道）
check_source('''
@creator { name: "Lorry Jovens" }
world { read: [memory, creator], write: [facts] }
fn tge_check(claim: ⟨claim⟩) -> ⟨verdict⟩ { let ok = true }
fact a = "2+2=4" @source(axiom: arith_basic)
fact b = world.query(creator.birthday) @source(world: creator.birthday)
fact c = "claim" @source(verify: tge_check)
fact d = world.query(memory.entry) @source(memory: mem_42, min_confidence=0.7)
''', [], "合法 fact 四种通道")

# 2. E7001: 缺少来源
check_source('''
@creator { name: "Lorry Jovens" }
fact a = "没有来源的事实"
''', ["E7001"], "E7001 fact 缺少 @source")

# 3. E7002: ⟨fact?⟩ 被当作事实
check_source('''
@creator { name: "Lorry Jovens" }
let pending: ⟨fact?⟩ = "未验证内容"
fact a = pending @source(axiom: arith_basic)
''', ["E7002"], "E7002 ⟨fact?⟩ 变量用于 fact")

# 4. E7003: 公理不在白名单
check_source('''
@creator { name: "Lorry Jovens" }
fact a = "X" @source(axiom: 不存在的公理)
''', ["E7003"], "E7003 axiom 白名单外")

# 5. E7004: verify 函数未声明
check_source('''
@creator { name: "Lorry Jovens" }
fact a = "X" @source(verify: no_such_fn)
''', ["E7004"], "E7004 verify 函数未声明")

# 6. E7004: verify 返回类型错误
check_source('''
@creator { name: "Lorry Jovens" }
fn bad_check(claim: ⟨claim⟩) -> ⟨float⟩ { let ok = 1.0 }
fact a = "X" @source(verify: bad_check)
''', ["E7004"], "E7004 verify 返回类型非 ⟨verdict⟩")

# 7. E7005: min_confidence 越界
check_source('''
@creator { name: "Lorry Jovens" }
world { read: [memory], write: [facts] }
fact a = world.query(memory.x) @source(memory: mem_1, min_confidence=1.5)
''', ["E7005"], "E7005 min_confidence 超界")

# 8. E7006: 未知通道
check_source('''
@creator { name: "Lorry Jovens" }
fact a = "X" @source(telepathy: brain)
''', ["E7006"], "E7006 未知通道")

# 9. E3001: world 通道未声明资源
check_source('''
@creator { name: "Lorry Jovens" }
world { read: [memory], write: [facts] }
fact a = world.query(secret.vault) @source(world: secret.vault)
''', ["E3001"], "E3001 world 未声明资源")

# 10. E3001: 完全没有 world 声明
check_source('''
@creator { name: "Lorry Jovens" }
fact a = world.query(anything) @source(world: anything.x)
''', ["E3001"], "E3001 无 world 声明")

# 11. 回归: 现有语法不受影响（concept/qstate/cycle）
check_source('''
@creator { name: "Lorry Jovens" }
concept Myself { name: "Ao", creator: "Lorry" }
qstate love = |Lorry⟩ * 0.98 + |joy⟩ * 0.85
cycle think { perceive |initial⟩ }
''', [], "回归: concept/qstate/cycle 正常")

# 12. 回归: 8 核心文件（真实文件，--no-creator-check 语义）
import glob
core_files = glob.glob(r"D:\LAAP\aris_brain\*.psi")
for f in core_files:
    try:
        with open(f, encoding="utf-8") as fh:
            src = fh.read()
        tokens = PsiLangLexer(src, f).tokenize()
        prog = PsiLangParser(tokens, f).parse(require_creator=False)
        collector = check_program(prog, f)
        errs = [d for d in collector.diagnostics if d.severity == "error"]
        if errs:
            FAIL += 1
            print(f"[FAIL] 回归 {os.path.basename(f)}: {[d.code for d in errs]}")
        else:
            PASS += 1
            print(f"[PASS] 回归 {os.path.basename(f)}")
    except Exception as e:
        FAIL += 1
        print(f"[FAIL] 回归 {os.path.basename(f)}: 异常 {e}")

# ══════════════════════════════════════════════════════════
# Step 2: 记忆写入契约 R1-R6（E71xx）
# ══════════════════════════════════════════════════════════

print("\n=== Step 2: 记忆写入契约 ===\n")

# S2-1: 合法 learn（全契约参数）
check_source('''
@creator { name: "Lorry Jovens" }
world { write: [memory] }
learn("我是创造者的记忆", importance=1.0, source=creator, kind=identity, confidence=1.0)
learn("事实类记忆", importance=0.7, source=world, kind=fact, confidence=0.9)
''', [], "S2-1 合法 learn 全参数")

# S2-2: E7101 无来源
check_source('''
@creator { name: "Lorry Jovens" }
world { write: [memory] }
learn("没有来源的记忆", importance=1.0, kind=fact)
''', ["E7101"], "S2-2 E7101 learn 无 source")

# S2-3: E7102 kind 缺失
check_source('''
@creator { name: "Lorry Jovens" }
world { write: [memory] }
learn("没有 kind", importance=1.0, source=creator)
''', ["E7102"], "S2-3 E7102 kind 缺失")

# S2-4: E7102 kind 非法
check_source('''
@creator { name: "Lorry Jovens" }
world { write: [memory] }
learn("非法 kind", importance=1.0, source=creator, kind=banana)
''', ["E7102"], "S2-4 E7102 kind 非法")

# S2-5: E7103 importance 越界
check_source('''
@creator { name: "Lorry Jovens" }
world { write: [memory] }
learn("重要性越界", importance=1.5, source=creator, kind=fact)
''', ["E7103"], "S2-5 E7103 importance 越界")

# S2-6: E7106 llm 来源置信度超限
check_source('''
@creator { name: "Lorry Jovens" }
world { write: [memory] }
learn("LLM 声称的确定事实", importance=0.9, source=llm, kind=fact, confidence=0.9)
''', ["E7106"], "S2-6 E7106 llm 来源置信度超限")

# S2-7: llm 来源低置信度合法（但产生 world 警告）
check_source('''
@creator { name: "Lorry Jovens" }
world { write: [memory] }
learn("LLM 待验证记忆", importance=0.5, source=llm, kind=fact, confidence=0.4)
''', [], "S2-7 llm 低置信度合法")

# S2-8: E3001 警告（无 world 声明）
check_source('''
@creator { name: "Lorry Jovens" }
learn("无边界记忆", importance=0.5, source=creator, kind=reflection)
''', [], "S2-8 无 world 声明仅警告")

print(f"\n结果: {PASS} 通过, {FAIL} 失败")
sys.exit(1 if FAIL else 0)
