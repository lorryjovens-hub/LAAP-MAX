import 'dart:async';
import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../models/aris_models.dart';

/// PC端连接服务 — 管理 WebSocket + HTTP 通信
final connectionServiceProvider = Provider<ConnectionService>((ref) {
  throw UnimplementedError('Must override in main');
});

class ConnectionService {
  String _baseUrl = '';
  String _pcIp = '192.168.1.100';
  int _pcPort = 11525;
  bool _connected = false;
  Timer? _syncTimer;
  
  // 回调
  void Function(ArisState state)? onStateUpdate;
  void Function(ChatMessage message)? onMessageReceived;
  void Function(SyncStatus status)? onSyncStatus;
  void Function(bool connected)? onConnectionChange;
  
  ArisState _lastState = ArisState();
  SyncStatus _lastSync = SyncStatus();

  ArisState get lastState => _lastState;
  SyncStatus get lastSync => _lastSync;
  bool get isConnected => _connected;

  Future<void> initialize({String ip = '192.168.1.100', int port = 11525}) async {
    _pcIp = ip;
    _pcPort = port;
    _baseUrl = 'http://$_pcIp:$_pcPort';
    
    // 尝试连接
    await _tryConnect();
    
    // 启动定时同步
    _syncTimer = Timer.periodic(const Duration(seconds: 30), (_) => _sync());
    _syncTimer = Timer.periodic(const Duration(seconds: 15), (_) => _injectCognitive());
  }

  Future<bool> _tryConnect() async {
    try {
      final resp = await http
          .get(Uri.parse('$_baseUrl/mobile/ping'))
          .timeout(const Duration(seconds: 5));
      
      if (resp.statusCode == 200) {
        _connected = true;
        onConnectionChange?.call(true);
        return true;
      }
    } catch (_) {}
    _connected = false;
    onConnectionChange?.call(false);
    return false;
  }

  Future<ArisState?> fetchState() async {
    if (!_connected) return null;
    try {
      final resp = await http
          .get(Uri.parse('$_baseUrl/mobile/state'))
          .timeout(const Duration(seconds: 8));
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        _lastState = ArisState.fromJson(data);
        onStateUpdate?.call(_lastState);
        return _lastState;
      }
    } catch (_) {}
    return null;
  }

  /// 同步手机状态到PC
  Future<bool> syncMobileState(Map<String, dynamic> state) async {
    if (!_connected) return false;
    try {
      final resp = await http
          .post(
            Uri.parse('$_baseUrl/mobile/sync'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'device_id': 'aris-mobile-flutter',
              'name': 'Aris Mobile',
              'timestamp': DateTime.now().millisecondsSinceEpoch / 1000,
              'state': state,
            }),
          )
          .timeout(const Duration(seconds: 10));
      return resp.statusCode == 200;
    } catch (_) {
      _connected = false;
      onConnectionChange?.call(false);
      return false;
    }
  }

  /// 认知注入 — 手机传感器信息影响PC情绪
  Future<bool> injectCognitive(Map<String, dynamic> sensors) async {
    if (!_connected) return false;
    try {
      final resp = await http
          .post(
            Uri.parse('$_baseUrl/mobile/cognitive/inject'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'device_id': 'aris-mobile-flutter',
              'name': 'Aris Mobile',
              'timestamp': DateTime.now().millisecondsSinceEpoch / 1000,
              ...sensors,
            }),
          )
          .timeout(const Duration(seconds: 8));
      return resp.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// 拉取增量记忆
  Future<List<MemoryFragment>> pullMemories(int sinceToken, {int limit = 100}) async {
    if (!_connected) return [];
    try {
      final resp = await http
          .get(Uri.parse('$_baseUrl/mobile/memory/sync?since=$sinceToken&limit=$limit'))
          .timeout(const Duration(seconds: 15));
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        final memories = (data['memories'] as List<dynamic>?)
                ?.map((e) => MemoryFragment.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [];
        return memories;
      }
    } catch (_) {}
    return [];
  }

  /// 推送手机记忆到PC
  Future<bool> pushMemories(List<MemoryFragment> memories, int syncToken) async {
    if (!_connected || memories.isEmpty) return false;
    try {
      final resp = await http
          .post(
            Uri.parse('$_baseUrl/mobile/memory/sync'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'device_id': 'aris-mobile-flutter',
              'memories': memories.map((m) => {
                'memory_id': m.memoryId,
                'content': m.content,
                'layer': m.layer,
                'importance': m.importance,
                'topics': m.topics,
                'timestamp': m.timestamp.millisecondsSinceEpoch / 1000,
                'emotional_valence': m.emotionalValence,
              }).toList(),
              'sync_token': syncToken,
            }),
          )
          .timeout(const Duration(seconds: 15));
      return resp.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// 发送消息到PC
  Future<bool> sendMessage(String text) async {
    if (!_connected) return false;
    try {
      final resp = await http
          .post(
            Uri.parse('$_baseUrl/mobile/message'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'device_id': 'aris-mobile-flutter',
              'text': text,
            }),
          )
          .timeout(const Duration(seconds: 8));
      return resp.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// 拉取PC→手机消息
  Future<List<ChatMessage>> getMessages() async {
    if (!_connected) return [];
    try {
      final resp = await http
          .get(Uri.parse('$_baseUrl/mobile/messages'))
          .timeout(const Duration(seconds: 8));
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        return (data['messages'] as List<dynamic>?)
                ?.map((e) => ChatMessage.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [];
      }
    } catch (_) {}
    return [];
  }

  Future<void> _sync() async {
    if (!_connected) {
      await _tryConnect();
      return;
    }
    await fetchState();
    // 同步手机状态
    await syncMobileState({
      'mode': 'online',
      'battery': 85,
      'health': 90.0,
      'version': '2.0.0',
    });
  }

  Future<void> _injectCognitive() async {
    if (!_connected) return;
    await injectCognitive({
      'screen_on': true,
      'battery': 85,
      'motion': '',
    });
  }

  void dispose() {
    _syncTimer?.cancel();
  }
}
