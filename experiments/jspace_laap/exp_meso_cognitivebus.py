"""CognitiveBus 中观层五性质验证实验入口.

本模块作为 ``run_all.py`` 调用的入口，将逻辑委托给同目录下的
``runner.py``。runner 内部优先尝试导入 ``laap.agi.cognitive_bus``
真实实现；不可用时回退到轻量级 MockCognitiveBus。

需要验证的五个性质：
1. 可报告性（Reportability）
2. 可控性（Modulation）
3. 推理中介（Reasoning Mediation）
4. 灵活泛化（Flexible Generalization）
5. 选择性必要性（Selective Necessity）
"""

from __future__ import annotations

from experiments.jspace_laap.exp_meso_cognitivebus.runner import run

__all__ = ["run"]
