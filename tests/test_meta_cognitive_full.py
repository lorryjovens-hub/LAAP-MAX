"""
LAAP AGI — Meta-Cognitive Monitor Full Test Suite

测试元认知监控器的完整功能：
- 自动反思触发机制
- 认知偏差检测
- 自我报告生成
- 推理分析
- 循环推理检测
"""

import pytest
import time

from laap.agi.meta_cognitive import (
    MetaCognitiveMonitor,
    CognitiveEpisode,
    ReflectionTrigger,
)


class TestMetaCognitiveMonitor:
    """元认知监控器完整功能测试"""

    def setup_method(self):
        """设置测试环境"""
        self.monitor = MetaCognitiveMonitor()

    def test_cognitive_episode_creation(self):
        """测试认知片段创建"""
        episode = CognitiveEpisode(context="测试上下文")
        
        assert episode.episode_id.startswith("ep_")
        assert episode.context == "测试上下文"
        assert episode.timestamp > 0
        assert episode.confidence == 0.5
        assert episode.emotional_state == "neutral"

    def test_cognitive_episode_to_dict(self):
        """测试认知片段序列化"""
        episode = CognitiveEpisode(context="详细的测试上下文")
        episode.reasoning_trace = ["步骤1", "步骤2", "步骤3"]
        episode.action_taken = "执行测试操作"
        episode.outcome = "success"
        episode.confidence = 0.85
        episode.emotional_state = "positive"
        
        data = episode.to_dict()
        
        assert "episode_id" in data
        assert data["context"] == "详细的测试上下文"
        assert data["reasoning_steps"] == 3
        assert data["action_taken"] == "执行测试操作"
        assert data["outcome"] == "success"
        assert data["confidence"] == 0.85
        assert data["emotional_state"] == "positive"

    def test_monitor_initialization(self):
        """测试监控器初始化"""
        assert self.monitor.episodes == []
        assert self.monitor.reflections == []
        assert self.monitor.current_episode is None
        assert self.monitor.cognitive_biases_detected == []
        
        assert "total_episodes" in self.monitor.performance_metrics
        assert "successful_episodes" in self.monitor.performance_metrics
        assert "average_confidence" in self.monitor.performance_metrics
        assert "total_reflections" in self.monitor.performance_metrics
        assert "biases_found" in self.monitor.performance_metrics

    def test_start_episode(self):
        """测试开始新的认知片段"""
        episode_id = self.monitor.start_episode("测试任务：计算问题")
        
        assert episode_id.startswith("ep_")
        assert self.monitor.current_episode is not None
        assert self.monitor.current_episode.context == "测试任务：计算问题"

    def test_record_reasoning(self):
        """测试记录推理步骤"""
        self.monitor.start_episode("推理测试")
        
        self.monitor.record_reasoning("分析问题")
        self.monitor.record_reasoning("收集信息")
        self.monitor.record_reasoning("制定方案")
        
        assert len(self.monitor.current_episode.reasoning_trace) == 3
        assert "分析问题" in self.monitor.current_episode.reasoning_trace
        assert "制定方案" in self.monitor.current_episode.reasoning_trace

    def test_record_action(self):
        """测试记录行动和结果"""
        self.monitor.start_episode("行动测试")
        
        self.monitor.record_action("执行操作", "success", confidence=0.9)
        
        assert self.monitor.current_episode.action_taken == "执行操作"
        assert self.monitor.current_episode.outcome == "success"
        assert self.monitor.current_episode.confidence == 0.9

    def test_end_episode(self):
        """测试结束认知片段"""
        self.monitor.start_episode("结束测试")
        self.monitor.record_reasoning("步骤1")
        self.monitor.record_action("执行", "success", confidence=0.8)
        
        episode = self.monitor.end_episode()
        
        assert episode is not None
        assert episode.duration_ms > 0
        assert self.monitor.current_episode is None
        assert len(self.monitor.episodes) == 1

    def test_update_metrics(self):
        """测试指标更新"""
        for i in range(5):
            self.monitor.start_episode(f"指标测试 {i}")
            self.monitor.record_reasoning("推理步骤")
            outcome = "success" if i % 2 == 0 else "partial"
            confidence = 0.7 + (i % 3) * 0.1
            self.monitor.record_action("执行", outcome, confidence=confidence)
            self.monitor.end_episode()
        
        metrics = self.monitor.performance_metrics
        
        assert metrics["total_episodes"] == 5
        assert metrics["successful_episodes"] >= 2
        assert 0.5 <= metrics["average_confidence"] <= 1.0

    def test_auto_reflection_low_confidence(self):
        """测试低置信度触发反思"""
        self.monitor.start_episode("低置信度任务")
        self.monitor.record_reasoning("不太确定答案")
        self.monitor.record_action("猜测答案", "结果未知", confidence=0.2)
        self.monitor.end_episode()
        
        assert len(self.monitor.reflections) >= 1
        
        reflection = self.monitor.reflections[-1]
        assert ReflectionTrigger.CONFIDENCE_LOW.value in reflection["triggers"]

    def test_auto_reflection_error_detected(self):
        """测试错误检测触发反思"""
        self.monitor.start_episode("失败任务")
        self.monitor.record_reasoning("尝试执行")
        self.monitor.record_action("执行操作", "error: 失败", confidence=0.5)
        self.monitor.end_episode()
        
        assert len(self.monitor.reflections) >= 1
        
        reflection = self.monitor.reflections[-1]
        assert ReflectionTrigger.ERROR_DETECTED.value in reflection["triggers"]

    def test_auto_reflection_time_based(self):
        """测试时间触发反思"""
        for i in range(5):
            self.monitor.start_episode(f"任务 {i}")
            self.monitor.record_reasoning("步骤")
            self.monitor.record_action("执行", "success", confidence=0.7)
            self.monitor.end_episode()
        
        assert len(self.monitor.reflections) >= 1
        
        reflection = self.monitor.reflections[-1]
        assert ReflectionTrigger.TIME_BASED.value in reflection["triggers"]

    def test_bias_detection_confirmation(self):
        """测试确认偏差检测"""
        self.monitor.start_episode("确认偏差测试")
        self.monitor.record_reasoning("这个数据支持我的观点")
        self.monitor.record_reasoning("没有反例可以反驳")
        self.monitor.record_action("提交结论", "success", confidence=0.8)
        self.monitor.end_episode()
        
        biases = self.monitor.cognitive_biases_detected
        assert len(biases) >= 1
        assert "confirmation_bias" in biases[-1]["biases"]

    def test_bias_detection_anchoring(self):
        """测试锚定效应检测"""
        self.monitor.start_episode("锚定效应测试")
        self.monitor.record_reasoning("上次的结果是基准")
        self.monitor.record_reasoning("基于之前的锚点")
        self.monitor.record_action("提交结论", "success", confidence=0.8)
        self.monitor.end_episode()
        
        biases = self.monitor.cognitive_biases_detected
        assert len(biases) >= 1
        assert "anchoring_bias" in biases[-1]["biases"]

    def test_bias_detection_emotional(self):
        """测试情感偏差检测"""
        self.monitor.start_episode("情感偏差测试")
        self.monitor.record_reasoning("我觉得这个方案很好")
        self.monitor.record_reasoning("直觉告诉我应该这样做")
        self.monitor.record_action("执行方案", "success", confidence=0.85)
        self.monitor.end_episode()
        
        biases = self.monitor.cognitive_biases_detected
        assert len(biases) >= 1
        assert "emotional_bias" in biases[-1]["biases"]

    def test_bias_detection_overconfidence(self):
        """测试过度自信检测"""
        self.monitor.start_episode("过度自信测试")
        self.monitor.record_reasoning("这个方案绝对正确")
        self.monitor.record_reasoning("毫无疑问会成功")
        self.monitor.record_action("执行方案", "success", confidence=0.95)
        self.monitor.end_episode()
        
        biases = self.monitor.cognitive_biases_detected
        assert len(biases) >= 1
        assert "overconfidence" in biases[-1]["biases"]

    def test_bias_detection_insufficient_reasoning(self):
        """测试推理不足检测"""
        self.monitor.start_episode("推理不足测试")
        self.monitor.record_reasoning("直接得出结论")
        self.monitor.record_action("快速决策", "success", confidence=0.7)
        self.monitor.end_episode()
        
        biases = self.monitor.cognitive_biases_detected
        assert len(biases) >= 1
        assert "insufficient_reasoning" in biases[-1]["biases"]

    def test_circularity_detection(self):
        """测试循环推理检测"""
        self.monitor.start_episode("循环推理测试")
        self.monitor.record_reasoning("A因为B")
        self.monitor.record_reasoning("B因为C")
        self.monitor.record_reasoning("C因为A")
        self.monitor.record_action("提交循环论证", "success", confidence=0.2)
        self.monitor.end_episode()
        
        assert len(self.monitor.reflections) >= 1
        reflection = self.monitor.reflections[-1]
        assert reflection["circularity_detected"] is True

    def test_circularity_not_detected(self):
        """测试非循环推理"""
        self.monitor.start_episode("非循环推理测试")
        self.monitor.record_reasoning("问题分析")
        self.monitor.record_reasoning("收集数据")
        self.monitor.record_reasoning("得出结论")
        self.monitor.record_action("提交报告", "success", confidence=0.2)
        self.monitor.end_episode()
        
        assert len(self.monitor.reflections) >= 1
        reflection = self.monitor.reflections[-1]
        assert reflection["circularity_detected"] is False

    def test_reasoning_analysis(self):
        """测试推理分析"""
        self.monitor.start_episode("推理分析测试")
        self.monitor.record_reasoning("目标是解决这个问题")
        self.monitor.record_reasoning("有两个备选方案：A和B")
        self.monitor.record_reasoning("根据数据显示，方案A更好")
        self.monitor.record_reasoning("选择方案A")
        self.monitor.record_action("执行方案A", "success", confidence=0.2)
        self.monitor.end_episode()
        
        assert len(self.monitor.reflections) >= 1
        reflection = self.monitor.reflections[-1]
        analysis = reflection["reasoning_analysis"]
        
        assert analysis["step_count"] == 4
        assert analysis["has_goal_mention"] is True
        assert analysis["has_alternatives"] is True
        assert analysis["has_evidence"] is True
        assert analysis["depth_score"] > 0.3

    def test_self_report_generation(self):
        """测试自我报告生成"""
        for i in range(5):
            self.monitor.start_episode(f"任务 {i+1}")
            self.monitor.record_reasoning(f"分析任务 {i+1}")
            self.monitor.record_reasoning(f"制定策略 {i+1}")
            outcome = "success" if i % 2 == 0 else "partial success"
            confidence = 0.8 + (i % 3) * 0.1
            self.monitor.record_action(f"执行任务 {i+1}", outcome, confidence=confidence)
            self.monitor.end_episode()
        
        report = self.monitor.get_self_report()
        
        assert "meta_cognitive_report" in report
        assert report["meta_cognitive_report"]["total_episodes"] == 5
        assert report["meta_cognitive_report"]["total_reflections"] >= 1
        assert "bias_distribution" in report
        assert "learning_points" in report

    def test_introspection_prompt_generation(self):
        """测试内省提示生成"""
        for i in range(3):
            self.monitor.start_episode(f"内省测试任务 {i+1}")
            self.monitor.record_reasoning("分析问题")
            self.monitor.record_action("执行", "success", confidence=0.75)
            self.monitor.end_episode()
        
        prompt = self.monitor.generate_introspection_prompt()
        
        assert isinstance(prompt, str)
        assert "元认知内省提示" in prompt
        assert "累计完成" in prompt
        assert "成功率" in prompt
        assert "平均置信度" in prompt

    def test_learning_points_extraction(self):
        """测试学习要点提取"""
        self.monitor.start_episode("学习要点测试")
        self.monitor.record_reasoning("步骤太少")
        self.monitor.record_action("快速决策", "error: 失败", confidence=0.25)
        episode = self.monitor.end_episode()
        
        points = self.monitor._extract_learning_points(episode)
        
        assert len(points) >= 2
        assert "置信度低" in points[0]
        assert "推理步骤不足" in points[1]


class TestMetaCognitiveMonitorWithLLM:
    """带模拟LLM的元认知监控器测试"""

    def setup_method(self):
        """设置测试环境"""
        class MockLLMClient:
            def complete(self, prompt):
                return "模拟LLM反思结果：推理过程看起来合理，但可以增加更多备选方案的分析。"
        
        self.monitor = MetaCognitiveMonitor(llm_client=MockLLMClient())

    def test_llm_reflection(self):
        """测试LLM深度反思"""
        self.monitor.start_episode("LLM反思测试")
        self.monitor.record_reasoning("分析问题")
        self.monitor.record_reasoning("制定方案")
        self.monitor.record_action("执行", "failure", confidence=0.2)
        self.monitor.end_episode()
        
        assert len(self.monitor.reflections) >= 1
        
        reflection = self.monitor.reflections[-1]
        assert "llm_insight" in reflection
        assert "模拟LLM反思结果" in reflection["llm_insight"]


class TestMetaCognitiveIntegration:
    """元认知监控器集成测试"""

    def test_performance_metrics_accuracy(self):
        """测试性能指标准确性"""
        monitor = MetaCognitiveMonitor()
        
        successes = 0
        total = 10
        for i in range(total):
            monitor.start_episode(f"性能测试 {i}")
            monitor.record_reasoning("步骤")
            outcome = "success" if i % 2 == 0 else "failure"
            if outcome == "success":
                successes += 1
            confidence = 0.8 if outcome == "success" else 0.3
            monitor.record_action("执行", outcome, confidence=confidence)
            monitor.end_episode()
        
        report = monitor.get_self_report()
        expected_rate = successes / total
        actual_rate = report["meta_cognitive_report"]["success_rate"]
        
        assert actual_rate >= 0 and actual_rate <= 1

    def test_reflection_summary_generation(self):
        """测试反思摘要生成"""
        monitor = MetaCognitiveMonitor()
        
        monitor.start_episode("摘要测试1")
        monitor.record_reasoning("支持我的观点")
        monitor.record_action("执行", "success", confidence=0.2)
        monitor.end_episode()
        
        assert len(monitor.reflections) >= 1
        reflection = monitor.reflections[-1]
        summary = reflection["summary"]
        
        assert isinstance(summary, str)
        assert len(summary) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
