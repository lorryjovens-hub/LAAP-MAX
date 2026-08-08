"""感知器官标准接口 - 意识系统感知层的抽象基类

遵循 0-token 优先原则：所有感知器官应优先使用确定性算法完成结构化提取，
仅在算法无法覆盖的语义维度上调用 LLM，以最小化 token 消耗。
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.utils.logger import get_logger

logger = get_logger(__name__)

# 感知流水线各阶段的类型变量
RawInputT = TypeVar("RawInputT")          # 原始输入类型
PreprocessedT = TypeVar("PreprocessedT")  # 预处理后数据
FeatureT = TypeVar("FeatureT")            # 特征集
StructuredT = TypeVar("StructuredT")     # 结构化输出
AnnotatedT = TypeVar("AnnotatedT")       # 语义标注后最终输出


class PerceptionOrgan(
    ABC,
    Generic[RawInputT, PreprocessedT, FeatureT, StructuredT, AnnotatedT],
):
    """
    感知器官标准接口

    所有感知器官（视觉、爬虫、布局、视频、内部状态）必须实现此接口。
    通过模板方法模式定义统一感知流水线：
        preprocess → extract_features → structured_output → semantic_annotate

    遵循 0-token 优先原则：
    - 优先使用确定性算法完成结构化提取（preprocess / extract_features / structured_output）
    - 仅在语义维度无法由算法覆盖时调用 LLM（semantic_annotate）
    - LLM 调用必须以高密度载荷为输入，避免冗余 token 消耗

    子类约定：各阶段中间结果通过实例属性传递，命名建议以单下划线前缀标识
    （如 ``self._preprocessed``、``self._features``、``self._structured``）。
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"perception.{name}")

    def perceive(self, raw: RawInputT) -> AnnotatedT:
        """
        模板方法：按顺序执行感知流水线

        1. preprocess(raw)     - 原始数据预处理与归一化
        2. extract_features()  - 特征提取（算法优先，0-token 路径）
        3. structured_output()  - 结构化输出（零 LLM token）
        4. semantic_annotate()  - 语义标注（必要时调用 LLM）

        Returns:
            语义标注后的最终感知结果
        """
        self.logger.info(f"[{self.name}] 感知流水线启动")

        self.preprocess(raw)
        self.logger.debug(f"[{self.name}] 预处理完成")

        self.extract_features()
        self.logger.debug(f"[{self.name}] 特征提取完成")

        self.structured_output()
        self.logger.debug(f"[{self.name}] 结构化输出完成")

        result = self.semantic_annotate()
        self.logger.info(f"[{self.name}] 感知流水线完成")

        return result

    @abstractmethod
    def preprocess(self, raw: RawInputT) -> PreprocessedT:
        """预处理：清洗、归一化、格式转换。中间结果存入实例属性。"""
        ...

    @abstractmethod
    def extract_features(self) -> FeatureT:
        """特征提取：算法优先，0-token 路径。读取预处理结果，存入实例属性。"""
        ...

    @abstractmethod
    def structured_output(self) -> StructuredT:
        """结构化输出：生成可直接消费的结构化数据，零 LLM token。"""
        ...

    @abstractmethod
    def semantic_annotate(self) -> AnnotatedT:
        """语义标注：必要时调用 LLM 补充语义信息，返回最终感知结果。"""
        ...
