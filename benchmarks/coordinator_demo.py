# -*- coding: utf-8 -*-
"""RSICoordinator 实况演示。"""
import sys, json
sys.path.insert(0, r'D:\LAAP')
from laap.evolution.rsi_coordinator import CodebaseSensor, RSICoordinator

sensor = CodebaseSensor(window_hours=6)
report = sensor.full_report()
print('=== 感知报告（最近 6 小时）===')
print(f'改动文件数: {report["change_count"]}')
print('最近 5 个改动:')
for c in report['recent_changes'][:5]:
    print(f'  {c["age_hours"]:5.2f}h  {c["path"]}')
g = report['git']
print(f'git: modified={g.get("modified")} untracked={g.get("untracked")}')
print(f'冲突: {len(report["conflicts"])}')
for cf in report['conflicts'][:3]:
    print(f'  [{cf["level"]}] {cf["dir"]} ({cf["count"]} 文件)')
print(f'成绩单: {json.dumps(report["ledger"], ensure_ascii=False)}')

print()
print('=== 协调管线演示 ===')
coord = RSICoordinator()
r = coord.coordinate('增强代码感知能力', ['laap/tools/a.py', 'laap/tools/b.py', 'laap/cognition/c.py'])
print(r.summary)
