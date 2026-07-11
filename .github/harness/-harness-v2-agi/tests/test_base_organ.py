"""PerceptionOrgan 抽象基类接口契约测试"""

import pytest

from src.consciousness.perception.base_organ import PerceptionOrgan


class ConcreteOrgan(PerceptionOrgan):
    """测试用的具体实现"""

    def __init__(self):
        super().__init__(name="concrete")

    def preprocess(self, raw):
        self._preprocessed = raw
        return raw

    def extract_features(self):
        self._features = {"features": "test"}
        return self._features

    def structured_output(self):
        self._structured = {"structured": "test"}
        return self._structured

    def semantic_annotate(self):
        return {"annotated": self._structured}


def test_perception_organ_is_abstract():
    """PerceptionOrgan 是抽象类，不能直接实例化"""
    with pytest.raises(TypeError):
        PerceptionOrgan(name="x")


def test_concrete_organ_implements_all_methods():
    """具体实现必须实现 4 个抽象方法"""
    organ = ConcreteOrgan()
    assert organ.preprocess("test") == "test"
    assert organ.extract_features() == {"features": "test"}
    assert organ.structured_output() == {"structured": "test"}
    # semantic_annotate 无参数（基类契约）
    result = organ.semantic_annotate()
    assert "annotated" in result


def test_perceive_template_method():
    """模板方法 perceive() 按序调用四个阶段（同步）"""
    organ = ConcreteOrgan()
    result = organ.perceive("raw_input")
    assert "annotated" in result
    # 中间状态应被填充
    assert organ._preprocessed == "raw_input"
    assert organ._features == {"features": "test"}
    assert organ._structured == {"structured": "test"}


def test_logger_exists():
    """每个器官实例应有 logger"""
    organ = ConcreteOrgan()
    assert hasattr(organ, "logger")
    assert organ.name == "concrete"


def test_name_attribute_set():
    """name 属性由 __init__ 设置"""
    organ = ConcreteOrgan()
    assert organ.name == "concrete"


def test_subclass_must_implement_abstract_methods():
    """缺少任意抽象方法都会触发 TypeError"""

    class MissingOne(PerceptionOrgan):
        def __init__(self):
            super().__init__(name="missing")

        def preprocess(self, raw):
            return raw

        def extract_features(self):
            return {}

        def structured_output(self):
            return {}

        # 缺少 semantic_annotate

    with pytest.raises(TypeError):
        MissingOne()
