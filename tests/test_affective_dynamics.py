"""
LAAP AGI — Affective Dynamics Test Suite

测试情感动力学引擎的完整功能：
- 人格轮廓对情感响应的影响
- 情感耦合矩阵的效果
- 认知偏置计算
- 情感状态演化
"""

import pytest
import numpy as np

from laap.agi.affective_engine import (
    EmotionDimension,
    PersonalityProfile,
    AffectiveState,
    AffectiveEventProcessor,
)


class TestAffectiveDynamics:
    """情感动力学引擎测试"""

    def test_emotion_dimension_enum(self):
        """测试情感维度枚举"""
        assert EmotionDimension.PLEASURE.value == 0
        assert EmotionDimension.AROUSAL.value == 1
        assert EmotionDimension.DOMINANCE.value == 2
        assert EmotionDimension.SOCIAL.value == 3
        assert EmotionDimension.STRESS.value == 4

    def test_personality_profile_default(self):
        """测试默认人格轮廓"""
        profile = PersonalityProfile()
        
        assert profile.name == "Default"
        assert profile.baseline.shape == (5,)
        assert profile.sensitivity.shape == (5,)
        assert profile.decay_rates.shape == (5,)
        assert profile.noise_amplitude == 0.05

    def test_personality_profile_custom(self):
        """测试自定义人格轮廓"""
        custom_baseline = np.array([0.2, 0.3, 0.1, 0.4, 0.0])
        custom_sensitivity = np.array([1.2, 0.8, 1.0, 1.5, 0.9])
        custom_decay = np.array([0.08, 0.12, 0.15, 0.05, 0.25])
        
        profile = PersonalityProfile(
            name="CustomPersonality",
            baseline=custom_baseline,
            sensitivity=custom_sensitivity,
            decay_rates=custom_decay,
            noise_amplitude=0.08,
        )
        
        np.testing.assert_array_equal(profile.baseline, custom_baseline)
        np.testing.assert_array_equal(profile.sensitivity, custom_sensitivity)
        np.testing.assert_array_equal(profile.decay_rates, custom_decay)
        assert profile.noise_amplitude == 0.08

    def test_personality_profile_invalid_input(self):
        """测试无效输入处理"""
        invalid_baseline = np.array([1.0])
        profile = PersonalityProfile(baseline=invalid_baseline)
        
        assert profile.baseline.shape == (5,)
        np.testing.assert_array_equal(profile.baseline, np.array([0.0, 0.0, 0.0, 0.0, 0.0]))

    def test_affective_state_initialization(self):
        """测试情感状态初始化"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        assert state.state_vector.shape == (5,)
        assert state.coupling_matrix.shape == (5, 5)
        np.testing.assert_array_equal(state.state_vector, profile.baseline)

    def test_coupling_matrix_structure(self):
        """测试耦合矩阵结构"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        coupling = state.coupling_matrix
        
        assert coupling[EmotionDimension.STRESS.value, EmotionDimension.PLEASURE.value] == -0.4
        assert coupling[EmotionDimension.SOCIAL.value, EmotionDimension.PLEASURE.value] == 0.3
        assert coupling[EmotionDimension.STRESS.value, EmotionDimension.AROUSAL.value] == 0.5
        assert coupling[EmotionDimension.AROUSAL.value, EmotionDimension.STRESS.value] == 0.2
        assert coupling[EmotionDimension.SOCIAL.value, EmotionDimension.AROUSAL.value] == 0.25

    def test_nonlinear_transfer_loss_aversion(self):
        """测试非线性传递函数的损失厌恶特性"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        test_input = np.array([0.5, -0.5, 0.0, 1.0, -1.0])
        output = state._nonlinear_transfer(test_input)
        
        assert output[0] > 0
        assert output[1] < 0
        assert output[2] == 0
        assert abs(output[1]) > abs(output[0])
        assert np.all(output >= -1) and np.all(output <= 1)

    def test_noise_generation(self):
        """测试1/f噪声生成"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        noise = state._generate_1f_noise(1000)
        assert noise.shape == (1000,)
        assert np.abs(np.mean(noise)) < 0.1
        assert np.abs(np.std(noise) - 1.0) < 0.1

    def test_affective_update_with_stimulus(self):
        """测试带刺激的情感状态更新"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        initial_state = state.state_vector.copy()
        stimulus = np.array([0.5, 0.0, 0.0, 0.0, 0.0])
        
        state.update(external_stimulus=stimulus, dt=0.1)
        
        assert not np.array_equal(state.state_vector, initial_state)
        assert state.state_vector[EmotionDimension.PLEASURE.value] > 0
        assert np.all(state.state_vector >= -1) and np.all(state.state_vector <= 1)

    def test_affective_update_no_stimulus(self):
        """测试无刺激的情感状态更新"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        for _ in range(100):
            state.update(dt=0.1)
        
        assert np.all(state.state_vector >= -1) and np.all(state.state_vector <= 1)

    def test_dominant_emotion_detection(self):
        """测试主导情感检测"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        state.state_vector = np.array([0.8, 0.2, 0.1, 0.3, 0.4])
        dim, value = state.get_dominant_emotion()
        assert dim == EmotionDimension.PLEASURE
        assert value == 0.8
        
        state.state_vector = np.array([0.1, 0.9, 0.2, 0.3, 0.1])
        dim, value = state.get_dominant_emotion()
        assert dim == EmotionDimension.AROUSAL
        assert value == 0.9

    def test_valence_arousal_extraction(self):
        """测试效价和唤醒度提取"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        state.state_vector = np.array([0.6, 0.4, 0.2, 0.3, 0.1])
        valence, arousal = state.get_valence_arousal()
        assert valence == 0.6
        assert arousal == 0.4

    def test_mood_computation_all_moods(self):
        """测试所有情绪状态的计算"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        state.state_vector = np.array([0.6, 0.4, 0.0, 0.0, 0.0])
        assert state.compute_mood() == "joyful"
        
        state.state_vector = np.array([0.4, 0.2, 0.0, 0.0, 0.0])
        assert state.compute_mood() == "content"
        
        state.state_vector = np.array([-0.6, 0.4, 0.0, 0.0, 0.0])
        assert state.compute_mood() == "angry"
        
        state.state_vector = np.array([-0.4, 0.2, 0.0, 0.0, 0.0])
        assert state.compute_mood() == "sad"
        
        state.state_vector = np.array([0.0, 0.6, 0.0, 0.0, 0.0])
        assert state.compute_mood() == "anxious"
        
        state.state_vector = np.array([0.0, -0.4, 0.0, 0.0, 0.0])
        assert state.compute_mood() == "calm"
        
        state.state_vector = np.array([0.4, -0.3, 0.0, 0.0, 0.0])
        assert state.compute_mood() == "relaxed"
        
        state.state_vector = np.array([-0.4, -0.3, 0.0, 0.0, 0.0])
        assert state.compute_mood() == "depressed"
        
        state.state_vector = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        assert state.compute_mood() == "neutral"

    def test_cognitive_bias_computation(self):
        """测试认知偏差计算"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        biases = state.compute_cognitive_bias()
        
        assert "optimism" in biases
        assert "risk_seeking" in biases
        assert "attention_narrowing" in biases
        assert "confirmation_bias" in biases
        assert "overconfidence" in biases
        assert "temporal_discounting" in biases
        assert "social_proximity" in biases
        assert "creativity" in biases
        
        for value in biases.values():
            assert -0.8 <= value <= 0.8

    def test_cognitive_bias_affective_influence(self):
        """测试情感状态对认知偏差的影响"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        state.state_vector = np.array([0.6, 0.3, 0.5, 0.4, 0.2])
        biases = state.compute_cognitive_bias()
        
        assert biases["optimism"] > 0
        assert biases["overconfidence"] > 0
        assert biases["social_proximity"] > 0

    def test_prompt_context_generation(self):
        """测试提示上下文生成"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        context = state.to_prompt_context()
        
        assert "mood" in context
        assert "dominant_emotion" in context
        assert "emotion_intensity" in context
        assert "valence" in context
        assert "arousal" in context
        assert "dimensions" in context
        assert "cognitive_biases" in context

    def test_event_processor_positive_events(self):
        """测试积极事件处理"""
        stimulus = AffectiveEventProcessor.process_event("user_positive_feedback")
        assert stimulus[EmotionDimension.PLEASURE.value] > 0
        assert stimulus[EmotionDimension.STRESS.value] < 0
        
        stimulus = AffectiveEventProcessor.process_event("task_success")
        assert stimulus[EmotionDimension.PLEASURE.value] > 0
        assert stimulus[EmotionDimension.DOMINANCE.value] > 0

    def test_event_processor_negative_events(self):
        """测试消极事件处理"""
        stimulus = AffectiveEventProcessor.process_event("user_negative_feedback")
        assert stimulus[EmotionDimension.PLEASURE.value] < 0
        assert stimulus[EmotionDimension.STRESS.value] > 0
        
        stimulus = AffectiveEventProcessor.process_event("task_failure")
        assert stimulus[EmotionDimension.PLEASURE.value] < 0
        assert stimulus[EmotionDimension.STRESS.value] > 0

    def test_event_processor_unknown_event(self):
        """测试未知事件处理"""
        stimulus = AffectiveEventProcessor.process_event("unknown_event")
        np.testing.assert_array_equal(stimulus, np.zeros(5))

    def test_event_processor_intensity(self):
        """测试事件强度调节"""
        stimulus = AffectiveEventProcessor.process_event("task_success", intensity=0.5)
        assert abs(stimulus[EmotionDimension.PLEASURE.value] - 0.2) < 0.01
        
        stimulus = AffectiveEventProcessor.process_event("task_success", intensity=2.0)
        assert stimulus[EmotionDimension.PLEASURE.value] <= 1.0
        assert stimulus[EmotionDimension.PLEASURE.value] > 0.5


class TestPersonalityInfluence:
    """人格轮廓对情感响应的影响测试"""

    def test_personality_sensitivity_affects_response(self):
        """测试敏感度影响情感响应"""
        sensitive_profile = PersonalityProfile(
            name="Sensitive",
            sensitivity=np.array([2.0, 1.0, 1.0, 1.0, 1.0]),
        )
        insensitive_profile = PersonalityProfile(
            name="Insensitive",
            sensitivity=np.array([0.5, 1.0, 1.0, 1.0, 1.0]),
        )
        
        sensitive_state = AffectiveState(sensitive_profile)
        insensitive_state = AffectiveState(insensitive_profile)
        
        stimulus = np.array([0.5, 0.0, 0.0, 0.0, 0.0])
        
        sensitive_state.update(external_stimulus=stimulus, dt=0.1)
        insensitive_state.update(external_stimulus=stimulus, dt=0.1)
        
        assert sensitive_state.state_vector[0] > insensitive_state.state_vector[0]

    def test_personality_decay_affects_persistence(self):
        """测试衰减率影响情感持续时间"""
        slow_decay_profile = PersonalityProfile(
            name="SlowDecay",
            decay_rates=np.array([0.01, 0.01, 0.01, 0.01, 0.01]),
        )
        fast_decay_profile = PersonalityProfile(
            name="FastDecay",
            decay_rates=np.array([0.8, 0.8, 0.8, 0.8, 0.8]),
        )
        
        slow_state = AffectiveState(slow_decay_profile)
        fast_state = AffectiveState(fast_decay_profile)
        
        stimulus = np.array([0.8, 0.0, 0.0, 0.0, 0.0])
        
        slow_state.update(external_stimulus=stimulus, dt=0.5)
        fast_state.update(external_stimulus=stimulus, dt=0.5)
        
        for _ in range(30):
            slow_state.update(dt=0.1)
            fast_state.update(dt=0.1)
        
        assert slow_state.state_vector[0] > fast_state.state_vector[0]

    def test_personality_baseline_sets_default_mood(self):
        """测试基线设置默认情绪"""
        happy_profile = PersonalityProfile(
            name="Happy",
            baseline=np.array([0.5, 0.3, 0.2, 0.4, 0.1]),
        )
        sad_profile = PersonalityProfile(
            name="Sad",
            baseline=np.array([-0.4, 0.2, -0.1, -0.2, 0.3]),
        )
        
        happy_state = AffectiveState(happy_profile)
        sad_state = AffectiveState(sad_profile)
        
        assert happy_state.compute_mood() in ["joyful", "content", "relaxed"]
        assert sad_state.compute_mood() in ["sad", "depressed"]


class TestCouplingMatrixEffects:
    """情感耦合矩阵效果测试"""

    def test_stress_reduces_pleasure(self):
        """测试压力降低愉悦感"""
        profile = PersonalityProfile(noise_amplitude=0.0)
        state = AffectiveState(profile)

        state.state_vector = np.array([0.5, 0.0, 0.0, 0.0, 0.8])
        initial_pleasure = state.state_vector[EmotionDimension.PLEASURE.value]

        state.update(dt=0.5)

        assert state.state_vector[EmotionDimension.PLEASURE.value] < initial_pleasure

    def test_social_positivity_enhances_pleasure(self):
        """测试社交积极增强愉悦感"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        state.state_vector = np.array([0.0, 0.0, 0.0, 0.8, 0.0])
        
        state.update(dt=0.5)
        
        assert state.state_vector[EmotionDimension.PLEASURE.value] > 0

    def test_stress_increases_arousal(self):
        """测试压力增加唤醒度"""
        profile = PersonalityProfile()
        state = AffectiveState(profile)
        
        state.state_vector = np.array([0.0, 0.0, 0.0, 0.0, 0.8])
        
        state.update(dt=0.5)
        
        assert state.state_vector[EmotionDimension.AROUSAL.value] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
