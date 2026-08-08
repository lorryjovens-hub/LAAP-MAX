# -*- coding: utf-8 -*-
"""记忆保留率 v0.2 复测：混合检索 vs 纯 LIKE 生产库对照。"""
import sys, time
sys.path.insert(0, '.'); sys.path.insert(0, r'D:\LAAP')
from recall_bench.backends.laap_vault import LaapVaultBackend
from recall_bench.backends.hybrid import HybridBackend
from recall_bench.runner import run_benchmark

t0 = time.time()
r_like = run_benchmark(LaapVaultBackend(), tag='RB_V02', live=True)
print(f'LIKE:   recall={r_like.recall_rate:.1%}  ({time.time()-t0:.1f}s)')

t0 = time.time()
base = LaapVaultBackend()
corpus = base.list_recent(limit=2000)
hybrid = HybridBackend(base)
hybrid.prewarm([c.content for c in corpus])
r_hy = run_benchmark(hybrid, tag='RB_V02', live=True)
print(f'HYBRID: recall={r_hy.recall_rate:.1%}  ({time.time()-t0:.1f}s)')
print(f'语料: {len(corpus)} 条 | 目标: >60% | 结果: {"PASS" if r_hy.recall_rate >= 0.6 else "FAIL"}')