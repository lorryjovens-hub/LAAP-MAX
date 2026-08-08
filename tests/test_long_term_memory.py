"""
Phase 2 长期记忆存储模块测试

验证指标：
- 写入接口功能完整性
- 检索接口功能完整性
- 记忆巩固与衰减机制
- 语义检索准确性
"""

import pytest
import tempfile
import time
from pathlib import Path
from laap.memory.long_term import (
    LongTermMemory, MemoryEntry, MemoryType, 
    ProceduralMemory, ProceduralStep
)


class TestLongTermMemoryBasic:
    """测试基本功能"""

    def setup_method(self):
        """创建临时数据库进行测试"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_memory.db"
        self.ltm = LongTermMemory(db_path=self.db_path)

    def teardown_method(self):
        """清理测试资源"""
        self.ltm.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_engine_initialization(self):
        """测试引擎初始化"""
        assert self.ltm is not None
        assert self.ltm._conn is not None
        assert self.ltm._db_path.exists()

    def test_store_and_retrieve_episodic(self):
        """测试情景记忆的存储和检索"""
        # 存储情景记忆
        mem_id = self.ltm.store_episodic(
            content="用户今天询问了关于Python编程的问题",
            title="Python问题",
            tags=["python", "question"],
            emotional_valence=0.5,
            importance=0.7
        )
        
        assert mem_id is not None
        assert len(mem_id) == 8
        
        # 检索记忆
        entry = self.ltm.get(mem_id)
        assert entry is not None
        assert entry.id == mem_id
        assert entry.content == "用户今天询问了关于Python编程的问题"
        assert entry.title == "Python问题"
        assert "python" in entry.tags
        assert entry.emotional_valence == 0.5
        assert entry.importance == 0.7

    def test_store_and_retrieve_semantic(self):
        """测试语义记忆的存储和检索"""
        mem_id = self.ltm.store_semantic(
            key="Python版本",
            content="Python 3.11 是最新的稳定版本，于2022年10月发布",
            tags=["python", "version"],
            importance=0.8,
            confidence=0.95
        )
        
        entry = self.ltm.get(mem_id)
        assert entry is not None
        assert entry.title == "Python版本"
        assert entry.memory_type == MemoryType.SEMANTIC
        assert entry.confidence == 0.95

    def test_store_and_retrieve_procedural(self):
        """测试程序记忆的存储和检索"""
        steps = [
            {"action": "打开终端", "expected_result": "终端窗口打开"},
            {"action": "输入命令", "parameters": {"command": "python script.py"}, "expected_result": "脚本执行"},
            {"action": "检查输出", "expected_result": "输出结果正确"}
        ]
        
        mem_id = self.ltm.store_procedural(
            name="运行Python脚本",
            steps=steps,
            description="如何运行Python脚本的步骤"
        )
        
        # 获取程序记忆（包含步骤）
        proc_mem = self.ltm.get_procedural(mem_id)
        assert proc_mem is not None
        assert proc_mem.title == "运行Python脚本"
        assert len(proc_mem.steps) == 3
        assert proc_mem.steps[0].action == "打开终端"
        assert proc_mem.steps[1].parameters == {"command": "python script.py"}

    def test_store_skill(self):
        """测试技能记忆的存储"""
        mem_id = self.ltm.store_skill(
            name="代码审查",
            description="能够审查Python代码，发现潜在问题",
            code="def review_code(code): ...",
            proficiency=0.7
        )
        
        entry = self.ltm.get(mem_id)
        assert entry is not None
        assert entry.memory_type == MemoryType.SKILL
        assert entry.metadata["proficiency"] == 0.7

    def test_update_memory(self):
        """测试更新记忆"""
        mem_id = self.ltm.store_episodic(
            content="原始内容",
            importance=0.5
        )
        
        # 更新记忆
        success = self.ltm.update(mem_id, content="更新后的内容", importance=0.8)
        assert success is True
        
        # 验证更新
        entry = self.ltm.get(mem_id)
        assert entry.content == "更新后的内容"
        assert entry.importance == 0.8

    def test_delete_memory(self):
        """测试删除记忆"""
        mem_id = self.ltm.store_episodic(content="要删除的记忆")
        
        # 删除记忆
        success = self.ltm.delete(mem_id)
        assert success is True
        
        # 验证删除
        entry = self.ltm.get(mem_id)
        assert entry is None


class TestLongTermMemoryRetrieval:
    """测试检索功能"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_memory.db"
        self.ltm = LongTermMemory(db_path=self.db_path)
        
        # 预填充测试数据
        self.ltm.store_episodic("用户询问Python编程", tags=["python", "coding"])
        self.ltm.store_episodic("用户询问机器学习", tags=["ml", "ai"])
        self.ltm.store_episodic("用户询问数据可视化", tags=["visualization", "charts"])
        self.ltm.store_semantic("Python", "Python是一种高级编程语言")
        self.ltm.store_semantic("Machine Learning", "机器学习是AI的一个分支")

    def teardown_method(self):
        self.ltm.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_text_search(self):
        """测试全文搜索"""
        results = self.ltm.search("Python")
        assert len(results) >= 1
        assert any("Python" in r.content for r in results)

    def test_semantic_search(self):
        """测试语义搜索"""
        results = self.ltm.semantic_search("编程语言")
        assert len(results) >= 1
        # 检查相似度分数
        for entry, sim in results:
            assert 0.0 <= sim <= 1.0

    def test_recall_by_type(self):
        """测试按类型召回"""
        results = self.ltm.recall(memory_type=MemoryType.SEMANTIC)
        assert len(results) == 2
        for r in results:
            assert r.memory_type == MemoryType.SEMANTIC

    def test_recall_by_emotion(self):
        """测试按情绪召回"""
        # 存储带情绪的记忆
        self.ltm.store_episodic("快乐的事情", emotional_valence=0.8)
        self.ltm.store_episodic("中性的事情", emotional_valence=0.0)
        self.ltm.store_episodic("悲伤的事情", emotional_valence=-0.8)
        
        # 搜索积极情绪的记忆
        positive_results = self.ltm.recall_by_emotion(0.8, tolerance=0.2)
        assert len(positive_results) >= 1
        assert positive_results[0].emotional_valence == 0.8

    def test_recall_recent(self):
        """测试召回最近的记忆"""
        # 等待一秒确保时间差异
        time.sleep(1)
        recent_mem_id = self.ltm.store_episodic("最新的记忆")
        
        results = self.ltm.recall_recent(hours=1)
        assert len(results) >= 1
        assert any(r.id == recent_mem_id for r in results)

    def test_search_by_tags(self):
        """测试按标签搜索"""
        results = self.ltm.search_by_tags(["python"])
        assert len(results) >= 1
        assert any("python" in r.tags for r in results)


class TestLongTermMemoryConsolidation:
    """测试记忆巩固与衰减"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_memory.db"
        self.ltm = LongTermMemory(db_path=self.db_path)

    def teardown_method(self):
        self.ltm.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_memory_strengthen(self):
        """测试记忆强化"""
        mem_id = self.ltm.store_episodic("测试记忆", importance=0.5)
        
        # 强化记忆
        self.ltm.consolidate(mem_id, strengthen_amount=0.3)
        
        entry = self.ltm.get(mem_id)
        assert entry.importance == 0.8

    def test_memory_access_count(self):
        """测试访问计数"""
        mem_id = self.ltm.store_episodic("测试访问计数")
        
        # 多次访问
        self.ltm.get(mem_id)
        self.ltm.get(mem_id)
        self.ltm.get(mem_id)
        
        entry = self.ltm.get(mem_id)
        assert entry.access_count == 4  # 3次get + 1次store后的初始

    def test_memory_decay(self):
        """测试记忆衰减"""
        # 存储低重要性的记忆
        for i in range(5):
            self.ltm.store_episodic(f"临时记忆{i}", importance=0.1)
        
        # 存储高重要性的记忆
        for i in range(3):
            self.ltm.store_episodic(f"重要记忆{i}", importance=0.8)
        
        # 模拟衰减（使用短时间阈值）
        removed = self.ltm.decay(threshold_days=0, min_importance=0.3)
        assert removed == 5
        
        # 验证高重要性记忆保留
        remaining = self.ltm.count()
        assert remaining == 3

    def test_relevance_score(self):
        """测试相关性分数计算"""
        mem_id = self.ltm.store_episodic("测试相关性", importance=0.8)
        
        entry = self.ltm.get(mem_id)
        assert 0.0 <= entry.relevance_score <= 1.0


class TestLongTermMemoryIntegration:
    """集成测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_memory.db"
        self.ltm = LongTermMemory(db_path=self.db_path)

    def teardown_method(self):
        self.ltm.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_workflow(self):
        """测试完整的记忆工作流"""
        # 1. 存储各种类型的记忆
        epi_id = self.ltm.store_episodic(
            "用户需要创建一个网站",
            title="网站开发请求",
            tags=["web", "development"],
            emotional_valence=0.3
        )
        
        sem_id = self.ltm.store_semantic(
            "React",
            "React是一个用于构建用户界面的JavaScript库",
            tags=["frontend", "javascript"]
        )
        
        proc_id = self.ltm.store_procedural(
            "创建React应用",
            steps=[
                {"action": "安装Node.js"},
                {"action": "创建React项目", "parameters": {"template": "typescript"}},
                {"action": "启动开发服务器"}
            ]
        )
        
        # 2. 检索记忆
        epi_entry = self.ltm.get(epi_id)
        sem_entry = self.ltm.get(sem_id)
        proc_mem = self.ltm.get_procedural(proc_id)
        
        assert epi_entry is not None
        assert sem_entry is not None
        assert proc_mem is not None
        assert len(proc_mem.steps) == 3
        
        # 3. 搜索测试
        search_results = self.ltm.search("React")
        assert len(search_results) >= 2  # React语义记忆 + 创建React应用程序记忆
        
        # 4. 统计摘要
        summary = self.ltm.summarize()
        assert summary["total"] == 3
        assert summary["by_type"][MemoryType.EPISODIC] == 1
        assert summary["by_type"][MemoryType.SEMANTIC] == 1
        assert summary["by_type"][MemoryType.PROCEDURAL] == 1

    def test_memory_lifecycle(self):
        """测试记忆完整生命周期"""
        # 创建
        mem_id = self.ltm.store_episodic("生命周期测试", importance=0.5)
        
        # 读取
        entry = self.ltm.get(mem_id)
        assert entry is not None
        
        # 更新
        self.ltm.update(mem_id, importance=0.7)
        entry = self.ltm.get(mem_id)
        assert entry.importance == 0.7
        
        # 巩固
        self.ltm.consolidate(mem_id, 0.2)
        entry = self.ltm.get(mem_id)
        assert entry.importance == pytest.approx(0.9)
        
        # 删除
        self.ltm.delete(mem_id)
        entry = self.ltm.get(mem_id)
        assert entry is None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
    
    # 演示长期记忆功能
    print("\n" + "="*60)
    print("Phase 2 长期记忆存储模块演示")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "demo.db"
        ltm = LongTermMemory(db_path=db_path)
        
        print("\n1. 存储不同类型的记忆:")
        
        # 情景记忆
        epi_id = ltm.store_episodic(
            "用户今天想要学习机器学习",
            title="学习请求",
            tags=["learning", "ml"],
            emotional_valence=0.6,
            importance=0.7
        )
        print(f"   情景记忆: {epi_id}")
        
        # 语义记忆
        sem_id = ltm.store_semantic(
            "深度学习",
            "深度学习是机器学习的一个分支，使用多层神经网络",
            tags=["ai", "ml"],
            confidence=0.9
        )
        print(f"   语义记忆: {sem_id}")
        
        # 程序记忆
        proc_id = ltm.store_procedural(
            "训练神经网络",
            steps=[
                {"action": "准备数据集"},
                {"action": "定义模型架构"},
                {"action": "训练模型"},
                {"action": "评估结果"}
            ]
        )
        print(f"   程序记忆: {proc_id}")
        
        print("\n2. 全文搜索 '学习':")
        results = ltm.search("学习")
        for r in results:
            print(f"   - [{r.memory_type}] {r.title}: {r.content[:30]}")
        
        print("\n3. 语义搜索 'AI技术':")
        results = ltm.semantic_search("AI技术")
        for r, sim in results:
            print(f"   - {r.title} (相似度: {sim:.3f})")
        
        print("\n4. 按情绪召回 (积极):")
        results = ltm.recall_by_emotion(0.5)
        for r in results:
            print(f"   - {r.title} (效价: {r.emotional_valence})")
        
        print("\n5. 记忆统计摘要:")
        summary = ltm.summarize()
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for k, v in value.items():
                    print(f"     {k}: {v}")
            else:
                print(f"   {key}: {value}")
        
        print("\n6. 记忆巩固演示:")
        entry = ltm.get(epi_id)
        print(f"   原始重要性: {entry.importance}")
        ltm.consolidate(epi_id, 0.2)
        entry = ltm.get(epi_id)
        print(f"   巩固后重要性: {entry.importance}")
        
        ltm.close()
    
    print("\n" + "="*60)
    print("Phase 2 长期记忆存储模块验证完成！")
    print("="*60)
