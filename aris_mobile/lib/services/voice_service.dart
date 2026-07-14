import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';

/// 语音服务 — 长按录音 + TTS 不间断
class VoiceService {
  stt.SpeechToText? _stt;
  FlutterTts? _tts;
  bool _isInitialized = false;
  bool _isListening = false;
  bool _isSpeaking = false;
  bool _isAvailable = false;

  final StreamController<String> _recognitionController =
      StreamController<String>.broadcast();
  final StreamController<bool> _listeningController =
      StreamController<bool>.broadcast();

  Stream<String> get recognitionStream => _recognitionController.stream;
  Stream<bool> get listeningStream => _listeningController.stream;
  bool get isListening => _isListening;
  bool get isSpeaking => _isSpeaking;
  bool get isAvailable => _isAvailable;

  Future<void> initialize() async {
    if (_isInitialized) return;
    try {
      _stt = stt.SpeechToText();
      _isAvailable = await _stt!.initialize(
        onError: (e) => debugPrint('STT error: $e'),
      );
      _tts = FlutterTts();
      await _tts!.setLanguage('zh-CN');
      await _tts!.setPitch(1.0);
      await _tts!.setSpeechRate(0.48);
      _tts!.setCompletionHandler(() {
        _isSpeaking = false;
      });
      _isInitialized = true;
      debugPrint('VoiceService ready. STT: $_isAvailable');
    } catch (e) {
      debugPrint('Voice init error: $e');
    }
  }

  Future<void> startListening() async {
    if (!_isInitialized || _isListening || _stt == null) return;
    try {
      _isListening = true;
      _listeningController.add(true);
      await _stt!.listen(
        onResult: (result) {
          if (result.finalResult) {
            _recognitionController.add(result.recognizedWords);
            _isListening = false;
            _listeningController.add(false);
          }
        },
        listenFor: const Duration(minutes: 5),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
        localeId: 'zh_CN',
      );
    } catch (e) {
      debugPrint('STT listen error: $e');
      _isListening = false;
      _listeningController.add(false);
    }
  }

  Future<void> stopListening() async {
    if (!_isInitialized || !_isListening || _stt == null) return;
    try {
      await _stt!.stop();
    } catch (_) {}
    _isListening = false;
    _listeningController.add(false);
  }

  Future<void> speak(String text) async {
    if (!_isInitialized || text.isEmpty || _tts == null) return;
    try {
      _isSpeaking = true;
      await _tts!.speak(text);
    } catch (e) {
      debugPrint('TTS error: $e');
      _isSpeaking = false;
    }
  }

  Future<void> stopSpeaking() async {
    try {
      await _tts?.stop();
    } catch (_) {}
    _isSpeaking = false;
  }

  void dispose() {
    stopListening();
    stopSpeaking();
    _recognitionController.close();
    _listeningController.close();
  }
}
