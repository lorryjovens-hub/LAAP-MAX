import 'dart:math';
import 'dart:async';

/// ============================================================
/// 动作映射系统 — 语音→口型 / 情绪→表情 / 呼吸心跳
/// ============================================================

/// 动作帧
class MotionFrame {
  double mouthOpen = 0;     // 0-1
  double eyeL = 1, eyeR = 1; // 0=闭, 1=开
  double browL = 0, browR = 0; // -1=降, 0=中, 1=升
  double headX = 0, headY = 0, headZ = 0; // 头部旋转
  double bodyX = 0, bodyY = 0; // 身体偏移
  double breathPhase = 0;
  double heartbeatPhase = 0;
}

/// 动作映射器 — 将语音/情绪映射到 VRM 骨骼动画
class MotionMapper {
  final MotionFrame currentFrame = MotionFrame();
  double time = 0;
  
  // 口型同步滤波器
  double _mouthTarget = 0;
  double _mouthVelocity = 0;
  
  // 情绪状态
  double joy = 0, anger = 0, sorrow = 0, surprise = 0;
  double _targetJoy = 0, _targetAnger = 0, _targetSorrow = 0, _targetSurprise = 0;
  
  // 生理节律
  double _breathRate = 0.33; // 呼吸频率
  double _heartRate = 1.2;   // 心跳频率 (72bpm)
  
  // Idle 动画参数
  final Random _random = Random();
  double _idleTimer = 0;
  double _idleAmplitude = 0;
  String _currentIdle = 'stand';

  /// 每帧更新
  void tick(double dt) {
    time += dt;
    currentFrame.breathPhase += dt * _breathRate;
    currentFrame.heartbeatPhase += dt * _heartRate;

    // 口型平滑
    final dtClamped = min(dt, 0.05);
    currentFrame.mouthOpen += (_mouthTarget - currentFrame.mouthOpen) * dtClamped * 20;

    // 表情平滑
    joy += (_targetJoy - joy) * dtClamped * 8;
    anger += (_targetAnger - anger) * dtClamped * 8;
    sorrow += (_targetSorrow - sorrow) * dtClamped * 8;
    surprise += (_targetSurprise - surprise) * dtClamped * 8;

    // 眉毛跟随表情
    currentFrame.browL = joy * 0.3 - sorrow * 0.4 + surprise * 0.5 + anger * 0.2;
    currentFrame.browR = joy * 0.3 - sorrow * 0.4 + surprise * 0.5 - anger * 0.2;

    // 呼吸动画
    final breath = sin(currentFrame.breathPhase * 2 * pi);
    currentFrame.bodyY = breath * 2;

    // 心跳微动
    final heartbeat = sin(currentFrame.heartbeatPhase * 2 * pi);
    if (heartbeat > 0.8) {
      currentFrame.bodyX += heartbeat * 0.3;
    }

    // Idle 动作切换
    _idleTimer -= dt;
    if (_idleTimer <= 0) {
      _idleTimer = 3 + _random.nextDouble() * 5;
      _currentIdle = ['stand', 'tilt', 'shift', 'blink'][_random.nextInt(4)];
      _idleAmplitude = 0.5 + _random.nextDouble() * 2;
    }

    // Idle 动作
    switch (_currentIdle) {
      case 'tilt':
        currentFrame.headZ = sin(time * 1.5) * _idleAmplitude;
        break;
      case 'shift':
        currentFrame.bodyX = sin(time * 2) * _idleAmplitude;
        break;
      case 'blink':
        currentFrame.eyeL = currentFrame.eyeR = 0.8 + sin(time * 20) * 0.2;
        break;
    }
  }

  /// 语音驱动口型
  void onSpeech(double intensity, double frequency) {
    _mouthTarget = intensity.clamp(0, 1);
    // 根据频率微调嘴型形状
    if (frequency > 500) {
      _mouthTarget *= 0.7; // 高频音嘴唇闭合更多
    }
  }

  /// 语音结束时
  void onSpeechEnd() {
    _mouthTarget = 0;
  }

  /// 设置情绪
  void setEmotion(String emotion, double intensity) {
    _targetJoy = _targetAnger = _targetSorrow = _targetSurprise = 0;
    switch (emotion) {
      case '喜悦': _targetJoy = intensity; break;
      case '悲伤': _targetSorrow = intensity; break;
      case '惊讶': _targetSurprise = intensity; break;
      case '生气': _targetAnger = intensity; break;
      case '平静': break; // 全部归零
    }
  }

  /// 随机视线
  double getLookX(double t) => sin(t * 0.7) * 0.3 + sin(t * 1.3) * 0.2;
  double getLookY(double t) => sin(t * 0.5) * 0.2 + cos(t * 1.1) * 0.15;

  void dispose() {}
}
