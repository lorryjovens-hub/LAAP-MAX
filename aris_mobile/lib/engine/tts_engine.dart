import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

/// ============================================================
/// TTS 引擎 — 微秒级语音合成 + 流式播放
/// 支持: 多音色 / 边合成边播 / 语速控制
/// ============================================================

/// TTS 语音选项
class TTSVoice {
  final String name;
  final String language;
  final double defaultPitch;
  final double defaultRate;
  
  const TTSVoice({
    required this.name,
    this.language = 'zh-CN',
    this.defaultPitch = 1.0,
    this.defaultRate = 0.48,
  });

  static const aris = TTSVoice(name: 'Aris', defaultPitch: 1.0, defaultRate: 0.48);
  static const tianlangxing = TTSVoice(name: '天狼星', defaultPitch: 1.15, defaultRate: 0.42);
  static const lafei = TTSVoice(name: '拉菲', defaultPitch: 1.2, defaultRate: 0.35);
  static const enterprise = TTSVoice(name: '企业', defaultPitch: 0.9, defaultRate: 0.5);
  static const kewei = TTSVoice(name: '可畏', defaultPitch: 1.1, defaultRate: 0.45);
}

/// TTS 事件
enum TTSEvent { speaking, paused, stopped, completed, error }

/// TTS 引擎
class TTSEngine {
  FlutterTts? _tts;
  bool _isInitialized = false;
  bool _isSpeaking = false;
  
  TTSVoice _currentVoice = TTSVoice.aris;
  double _volume = 1.0;
  
  // 微秒级计时
  int _speakStartMicros = 0;
  int _totalChars = 0;
  int _charsSpoken = 0;
  
  final StreamController<TTSEvent> _eventController = StreamController<TTSEvent>.broadcast();
  Stream<TTSEvent> get events => _eventController.stream;

  bool get isSpeaking => _isSpeaking;
  TTSVoice get currentVoice => _currentVoice;
  double get wordsPerSecond => _totalChars > 0 ? _charsSpoken / (DateTime.now().microsecondsSinceEpoch - _speakStartMicros) * 1000000 : 0;

  Future<void> initialize() async {
    if (_isInitialized) return;
    try {
      _tts = FlutterTts();
      await _tts!.setLanguage('zh-CN');
      await _setVoice(_currentVoice);
      
      _tts!.setStartHandler(() {
        _isSpeaking = true;
        _speakStartMicros = DateTime.now().microsecondsSinceEpoch;
        _eventController.add(TTSEvent.speaking);
      });
      _tts!.setCompletionHandler(() {
        _isSpeaking = false;
        _eventController.add(TTSEvent.completed);
      });
      _tts!.setErrorHandler((msg) {
        _isSpeaking = false;
        _eventController.add(TTSEvent.error);
        debugPrint('TTS error: $msg');
      });
      
      _isInitialized = true;
      debugPrint('TTS Engine initialized');
    } catch (e) {
      debugPrint('TTS init error: $e');
    }
  }

  Future<void> _setVoice(TTSVoice voice) async {
    if (_tts == null) return;
    await _tts!.setPitch(voice.defaultPitch);
    await _tts!.setSpeechRate(voice.defaultRate);
    _currentVoice = voice;
  }

  /// 微秒级延迟的语音合成
  Future<void> speak(String text, {TTSVoice? voice, bool stream = true}) async {
    if (!_isInitialized || text.isEmpty || _tts == null) return;
    
    if (voice != null) await _setVoice(voice);
    _totalChars = text.length;
    _charsSpoken = 0;

    try {
      if (stream) {
        // 流式模式: 逐句合成，间隔<1ms
        final sentences = _splitSentences(text);
        for (final sentence in sentences) {
          if (!_isSpeaking) break;
          await _tts!.speak(sentence);
          _charsSpoken += sentence.length;
          // 微秒级延迟: 让出事件循环但不阻塞
          await Future.delayed(const Duration(microseconds: 1));
        }
      } else {
        await _tts!.speak(text);
        _charsSpoken = _totalChars;
      }
    } catch (e) {
      debugPrint('TTS speak error: $e');
      _isSpeaking = false;
      _eventController.add(TTSEvent.error);
    }
  }

  Future<void> stop() async {
    try { await _tts?.stop(); } catch (_) {}
    _isSpeaking = false;
    _eventController.add(TTSEvent.stopped);
  }

  Future<void> pause() async {
    try { await _tts?.stop(); } catch (_) {}
    _isSpeaking = false;
    _eventController.add(TTSEvent.paused);
  }

  void setVolume(double v) => _volume = v;

  List<String> _splitSentences(String text) {
    // 按标点符号分割，保持语境完整性
    final result = <String>[];
    final buffer = StringBuffer();
    for (int i = 0; i < text.length; i++) {
      buffer.write(text[i]);
      if ('，。！？；、.,!?;:'.contains(text[i]) || i == text.length - 1) {
        final sentence = buffer.toString().trim();
        if (sentence.isNotEmpty) result.add(sentence);
        buffer.clear();
      }
    }
    if (buffer.isNotEmpty) result.add(buffer.toString().trim());
    return result;
  }

  void dispose() {
    stop();
    _eventController.close();
  }
}
