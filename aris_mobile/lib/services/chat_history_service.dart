import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

/// 对话记录 — 持久化消息存储
class ChatHistoryService {
  final List<ChatSession> _sessions = [];
  int _activeId = 0;
  static const _maxSessions = 20;

  List<ChatSession> get sessions => _sessions;
  ChatSession? get active => _sessions.isEmpty ? null : _sessions.firstWhere((s) => s.id == _activeId, orElse: () => _sessions.first);

  Future<void> load() async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/chat_history.json');
      if (await file.exists()) {
        final data = jsonDecode(await file.readAsString()) as List;
        _sessions.addAll(data.map((e) => ChatSession.fromJson(e as Map)));
        if (_sessions.isNotEmpty) _activeId = _sessions.first.id;
      }
    } catch (e) {
      debugPrint('Chat history load error: $e');
    }
    if (_sessions.isEmpty) {
      _sessions.add(ChatSession(id: 1, name: '默认会话'));
      _activeId = 1;
    }
  }

  Future<void> save() async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      await File('${dir.path}/chat_history.json').writeAsString(jsonEncode(_sessions.map((s) => s.toJson()).toList()));
    } catch (e) {
      debugPrint('Chat history save error: $e');
    }
  }

  ChatSession newSession() {
    final id = DateTime.now().millisecondsSinceEpoch;
    final s = ChatSession(id: id, name: '会话 ${_sessions.length + 1}');
    _sessions.insert(0, s);
    if (_sessions.length > _maxSessions) _sessions.removeLast();
    _activeId = id;
    save();
    return s;
  }

  void switchSession(int id) {
    if (_sessions.any((s) => s.id == id)) _activeId = id;
  }

  void deleteSession(int id) {
    _sessions.removeWhere((s) => s.id == id);
    if (_sessions.isEmpty) newSession();
    if (_activeId == id) _activeId = _sessions.first.id;
    save();
  }

  void addMessage(String text, bool isMine, {String type = 'text'}) {
    active?.messages.add(ChatMessage(text: text, isMine: isMine, type: type));
    save();
  }

  void clearActive() {
    active?.messages.clear();
    save();
  }
}

class ChatSession {
  final int id;
  String name;
  final List<ChatMessage> messages;
  ChatSession({required this.id, this.name = '', List<ChatMessage>? messages}) : messages = messages ?? [];

  Map<String, dynamic> toJson() => {'id': id, 'name': name, 'messages': messages.map((m) => m.toJson()).toList()};
  factory ChatSession.fromJson(Map d) => ChatSession(
    id: d['id'] as int,
    name: d['name'] as String? ?? '',
    messages: (d['messages'] as List?)?.map((e) => ChatMessage.fromJson(e)).toList() ?? [],
  );
}

class ChatMessage {
  final String text;
  final bool isMine;
  final String type;
  final DateTime time;
  ChatMessage({required this.text, required this.isMine, this.type = 'text', DateTime? time}) : time = time ?? DateTime.now();

  Map<String, dynamic> toJson() => {'text': text, 'isMine': isMine, 'type': type, 'time': time.toIso8601String()};
  factory ChatMessage.fromJson(Map d) => ChatMessage(text: d['text'], isMine: d['isMine'], type: d['type'] ?? 'text');
}
