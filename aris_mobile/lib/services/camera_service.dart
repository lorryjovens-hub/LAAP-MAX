import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:camera/camera.dart';

final cameraServiceProvider = Provider<CameraService>((ref) {
  throw UnimplementedError('Must override in main');
});

/// 摄像头服务 — 完整相机控制
class CameraService {
  CameraController? _controller;
  List<CameraDescription>? _cameras;
  bool _isInitialized = false;
  bool _isRecording = false;
  int _selectedCamera = 0;
  
  StreamController<CameraImage?>? _frameStreamController;

  CameraController? get controller => _controller;
  List<CameraDescription>? get cameras => _cameras;
  bool get isInitialized => _isInitialized;
  bool get isRecording => _isRecording;
  int get cameraCount => _cameras?.length ?? 0;
  bool get hasFrontCamera => _cameras?.any((c) => c.lensDirection == CameraLensDirection.front) ?? false;
  bool get hasBackCamera => _cameras?.any((c) => c.lensDirection == CameraLensDirection.back) ?? false;
  
  Stream<CameraImage?>? get frameStream => _frameStreamController?.stream;

  Future<void> initialize({int preferredCamera = 0}) async {
    if (_isInitialized) return;
    
    try {
      // 获取可用摄像头列表
      _cameras = await availableCameras();
      
      if (_cameras == null || _cameras!.isEmpty) {
        debugPrint('No cameras available');
        return;
      }
      
      // 选择摄像头（默认后置）
      _selectedCamera = preferredCamera.clamp(0, _cameras!.length - 1);
      
      // 初始化控制器
      _controller = CameraController(
        _cameras![_selectedCamera],
        ResolutionPreset.medium,
        enableAudio: true,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );
      
      await _controller!.initialize();
      _isInitialized = true;
      
      _frameStreamController = StreamController<CameraImage?>.broadcast();
      
      debugPrint('Camera initialized: ${_cameras![_selectedCamera].name}');
    } catch (e) {
      debugPrint('Camera init error: $e');
    }
  }

  /// 切换前后摄像头
  Future<bool> switchCamera() async {
    if (_cameras == null || _cameras!.length < 2) return false;
    
    try {
      // 停止当前
      await _controller?.dispose();
      
      // 切换到下一个
      _selectedCamera = (_selectedCamera + 1) % _cameras!.length;
      
      _controller = CameraController(
        _cameras![_selectedCamera],
        ResolutionPreset.medium,
        enableAudio: true,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );
      
      await _controller!.initialize();
      return true;
    } catch (e) {
      debugPrint('Switch camera error: $e');
      return false;
    }
  }

  /// 拍照
  Future<XFile?> takePicture() async {
    if (!_isInitialized || _controller == null) return null;
    
    try {
      final photo = await _controller!.takePicture();
      debugPrint('Photo taken: ${photo.path}');
      return photo;
    } catch (e) {
      debugPrint('Take picture error: $e');
      return null;
    }
  }

  /// 开始录像
  Future<bool> startVideoRecording() async {
    if (!_isInitialized || _controller == null || _isRecording) return false;
    
    try {
      await _controller!.startVideoRecording();
      _isRecording = true;
      return true;
    } catch (e) {
      debugPrint('Start recording error: $e');
      return false;
    }
  }

  /// 停止录像
  Future<XFile?> stopVideoRecording() async {
    if (!_isInitialized || _controller == null || !_isRecording) return null;
    
    try {
      final video = await _controller!.stopVideoRecording();
      _isRecording = false;
      return video;
    } catch (e) {
      debugPrint('Stop recording error: $e');
      _isRecording = false;
      return null;
    }
  }

  /// 设置闪光灯模式
  Future<void> setFlashMode(FlashMode mode) async {
    if (_controller == null) return;
    try {
      await _controller!.setFlashMode(mode);
    } catch (e) {
      debugPrint('Set flash error: $e');
    }
  }

  /// 设置缩放
  Future<void> setZoom(double level) async {
    if (_controller == null) return;
    try {
      await _controller!.setZoomLevel(level);
    } catch (e) {
      debugPrint('Set zoom error: $e');
    }
  }

  /// 获取当前摄像头方向
  CameraLensDirection get currentLensDirection =>
      _cameras?.elementAtOrNull(_selectedCamera)?.lensDirection ??
      CameraLensDirection.back;

  ResolutionPreset get resolutionPreset => ResolutionPreset.medium;

  void dispose() {
    _controller?.dispose();
    _frameStreamController?.close();
  }
}
