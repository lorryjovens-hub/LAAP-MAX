import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../main.dart';
import '../engine/motion_mapper.dart';
import '../engine/tts_engine.dart';
import '../engine/laap_character.dart';
import '../services/voice_service.dart';
import '../services/chat_history_service.dart';
import '../services/pc_command_service.dart';
import '../widgets/lafei_renderer.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});
  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> with TickerProviderStateMixin {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  bool _thinking = false;

  final GlobalKey<LafeiWidgetState> _l2dKey = GlobalKey();
  final MotionMapper _motion = MotionMapper();
  late Ticker _vrmTick;
  final TTSEngine _tts = TTSEngine();
  final VoiceService _voice = VoiceService();
  final ChatHistoryService _history = ChatHistoryService();
  final PCCommandService _pc = PCCommandService();

  List<LaapCharacter> _chars = [];
  LaapCharacter? _char;
  int _charIdx = 0;
  bool _loaded = false;

  bool _showSessions = false;
  bool _recording = false;
  StreamSubscription<String>? _recSub;
  bool _voiceReady = false;

  @override
  void initState() {
    super.initState();
    _vrmTick = createTicker((elapsed) {
      _motion.tick(1/60);
      if (mounted) setState(() {});
    })..start();
    _tts.initialize();
    _initVoice();
    _pc.init();
    _loadChars();
    _history.load();
  }

  Future<void> _initVoice() async {
    await _voice.initialize();
    if (mounted) setState(() => _voiceReady = _voice.isAvailable);
  }

  Future<void> _loadChars() async {
    try {
      final c = await LaapCharacter.loadAll();
      if (mounted) setState(() { _chars = c; _loaded = true; if (c.isNotEmpty) { _char = c[0]; } });
    } catch (_) { if (mounted) setState(() => _loaded = true); }
  }

  @override
  void dispose() {
    _input.dispose(); _scroll.dispose(); _vrmTick.dispose(); _tts.dispose(); _motion.dispose();
    _voice.dispose(); _recSub?.cancel();
    super.dispose();
  }

  List get _msgs => _history.active?.messages ?? [];

  Future<void> _send(String text) async {
    if (text.trim().isEmpty) return;
    final msg = text.trim(); _input.clear();
    _history.addMessage(msg, true);
    setState(() => _thinking = true);
    _scrollAfter();

    // PC指令
    if (msg.startsWith('/pc ') || msg.startsWith('/cmd ')) {
      final cmd = msg.startsWith('/pc ') ? msg.substring(4) : msg.substring(5);
      final result = await _pc.execute(cmd);
      if (!mounted) return;
      _history.addMessage(result, false);
      setState(() => _thinking = false);
      _scrollAfter();
      return;
    }

    // LLM
    final llm = ref.read(llmServiceProvider);
    try {
      final reply = await llm.chat(msg);
      if (!mounted) return;
      _history.addMessage(reply, false);
      setState(() => _thinking = false);
      _motion.onSpeech(0.8, 400); unawaited(_tts.speak(reply, stream: true));
      _l2dKey.currentState?.setSpeaking(1.0);
      Future.delayed(const Duration(milliseconds: 800), () { _motion.onSpeechEnd(); _l2dKey.currentState?.setSilent(); });
      _scrollAfter();
    } catch (_) { if (mounted) setState(() => _thinking = false); }
  }

  void _scrollAfter() {
    Future.delayed(const Duration(milliseconds: 80), () {
      if (_scroll.hasClients) _scroll.animateTo(_scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
    });
  }

  // ===== 语音输入 (修复) =====
  void _startRec() {
    if (!_voiceReady) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('语音识别未就绪'), duration: Duration(seconds: 1)));
      setState(() => _recording = false);
      return;
    }
    _voice.startListening();
    _recSub?.cancel();
    _recSub = _voice.recognitionStream.listen((text) {
      if (text.isNotEmpty && mounted) {
        _voice.stopListening();
        setState(() => _recording = false);
        _send(text);
      }
    });
    setState(() => _recording = true);
  }

  void _stopRec() {
    _voice.stopListening();
    _recSub?.cancel();
    setState(() => _recording = false);
  }

  @override
  Widget build(BuildContext context) {
    final llm = ref.watch(llmServiceProvider);
    final isLLM = llm.isInitialized;

    return Column(children: [
      // 角色选择 + 多窗口
      SizedBox(height: 50, child: Row(children: [
        Expanded(child: ListView.builder(
          scrollDirection: Axis.horizontal, padding: const EdgeInsets.only(left: 10, right: 4, top: 5, bottom: 5),
          itemCount: _chars.length + 1,
          itemBuilder: (_, i) {
            if (i == 0) {
              return GestureDetector(
                onTap: () => setState(() => _showSessions = !_showSessions),
                child: Container(width: 40, height: 40, margin: const EdgeInsets.only(right: 4),
                  decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withOpacity(0.08), border: Border.all(color: Colors.white.withOpacity(0.08))),
                  child: Icon(Icons.chat_bubble, size: 16, color: Colors.white.withOpacity(0.5))),
              );
            }
            final ci = i - 1; final sel = ci == _charIdx; final c = _chars[ci];
            return GestureDetector(
              onTap: () => setState(() { _charIdx = ci; _char = c; }),
              child: Container(width: 40, height: 40, margin: const EdgeInsets.only(right: 6),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: sel ? const LinearGradient(colors: [Color(0xFF00D4AA), Color(0xFF0088CC)]) : null,
                  color: sel ? null : Colors.white.withOpacity(0.05),
                  border: Border.all(color: sel ? const Color(0xFF00D4AA) : Colors.white.withOpacity(0.06))),
                child: Center(child: Text(c.displayName.isNotEmpty ? c.displayName[0] : '?',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: sel ? Colors.white : Colors.white.withOpacity(0.5))))),
            );
          },
        )),
        // LLM状态 + 新建会话
        Row(children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(color: (isLLM ? const Color(0xFF30D158) : const Color(0xFFFF9F0A)).withOpacity(0.12), borderRadius: BorderRadius.circular(4)),
            child: Text(isLLM ? 'LLM' : '本地', style: TextStyle(fontSize: 8, fontWeight: FontWeight.w600, color: isLLM ? const Color(0xFF30D158) : const Color(0xFFFF9F0A))),
          ),
          const SizedBox(width: 4),
          GestureDetector(
            onTap: () { _history.newSession(); setState(() {}); },
            child: Container(width: 36, height: 36, margin: const EdgeInsets.only(right: 8),
              decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withOpacity(0.06)),
              child: Icon(Icons.add, size: 18, color: Colors.white.withOpacity(0.5))),
          ),
        ]),
      ])),
      if (_char != null)
        Padding(padding: const EdgeInsets.only(bottom: 1),
          child: Text('${_char!.displayName} · ${_char!.source.isNotEmpty ? _char!.source : "LAAP"}', style: TextStyle(fontSize: 8, color: Colors.white.withOpacity(0.25)))),
      if (_showSessions) _buildSessionList(),

      // 拉菲 Live2D
      SizedBox(height: 180, child: LafeiWidget(key: _l2dKey, height: 180, isTalking: _thinking)),

      // 消息
      Expanded(child: _msgs.isEmpty && !_thinking
        ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.chat_bubble_outline, size: 32, color: Colors.white.withOpacity(0.08)),
            const SizedBox(height: 6),
            Text('发送消息或长按录音', style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.2))),
          ]))
        : ListView.builder(
            controller: _scroll, padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
            itemCount: _msgs.length + (_thinking ? 1 : 0),
            itemBuilder: (_, i) {
              if (i == _msgs.length && _thinking) return _dot3();
              final m = _msgs[i];
              return GestureDetector(
                onLongPress: () { Clipboard.setData(ClipboardData(text: m.text)); ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('已复制'), duration: Duration(seconds: 1))); },
                child: Padding(padding: const EdgeInsets.only(bottom: 4),
                  child: Align(alignment: m.isMine ? Alignment.centerRight : Alignment.centerLeft,
                    child: Container(
                      constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: m.isMine ? const Color(0xFF0071E3) : const Color(0xFF1C1C1E),
                        borderRadius: BorderRadius.only(topLeft: const Radius.circular(16), topRight: const Radius.circular(16),
                          bottomLeft: Radius.circular(m.isMine ? 16 : 4), bottomRight: Radius.circular(m.isMine ? 4 : 16))),
                      child: Text(m.text, style: const TextStyle(fontSize: 13.5, height: 1.45, color: Color(0xFFF5F5F7)))))));
            })),
      // 输入栏
      Container(
        padding: const EdgeInsets.fromLTRB(10, 4, 10, 12),
        decoration: BoxDecoration(color: const Color(0xFF1C1C1E), border: Border(top: BorderSide(color: Colors.white.withOpacity(0.06)))),
        child: Row(children: [
          GestureDetector(
            onLongPressStart: (_) => _startRec(),
            onLongPressEnd: (_) => _stopRec(),
            onLongPressCancel: () { if (_recording) _stopRec(); },
            child: AnimatedContainer(duration: const Duration(milliseconds: 200),
              width: 32, height: 32,
              decoration: BoxDecoration(shape: BoxShape.circle, color: _recording ? const Color(0xFFFF453A) : Colors.white.withOpacity(0.08)),
              child: Icon(_recording ? Icons.mic : Icons.mic_none, size: 15, color: _recording ? Colors.white : Colors.white.withOpacity(0.5))),
          ),
          if (_recording)
            const Padding(padding: EdgeInsets.only(left: 6), child: SizedBox(width: 10, height: 10, child: CircularProgressIndicator(strokeWidth: 1.5, color: Color(0xFFFF453A)))),
          const SizedBox(width: 6),
          Expanded(child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(color: const Color(0xFF2C2C2E), borderRadius: BorderRadius.circular(18)),
            child: TextField(
              controller: _input, style: const TextStyle(color: Color(0xFFF5F5F7), fontSize: 13.5),
              decoration: InputDecoration(border: InputBorder.none,
                hintText: '发消息给 Lorry... ($isLLM ? "LLM" : "本地")',
                hintStyle: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 12)),
              onSubmitted: _send))),
          const SizedBox(width: 6),
          GestureDetector(onTap: () => _send(_input.text),
            child: Container(width: 32, height: 32, decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(0xFF0071E3)),
              child: const Icon(Icons.arrow_upward, size: 15, color: Colors.white))),
        ]),
      ),
    ]);
  }

  Widget _buildSessionList() {
    final ss = _history.sessions;
    return Container(
      height: 180, margin: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(color: const Color(0xFF1A1A2E), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white.withOpacity(0.06))),
      child: Column(children: [
        Padding(padding: const EdgeInsets.fromLTRB(12, 8, 12, 4), child: Row(children: [
          const Text('多窗口', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFFF5F5F7))),
          const Spacer(),
          GestureDetector(onTap: () => _history.newSession(), child: Icon(Icons.add_circle_outline, size: 16, color: const Color(0xFF0071E3))),
        ])),
        Expanded(child: ListView.builder(itemCount: ss.length, itemBuilder: (_, i) {
          final s = ss[i]; final act = s.id == _history.active?.id;
          final prev = s.messages.isEmpty ? '(空)' : s.messages.last.text.substring(0, s.messages.last.text.length.clamp(0, 24));
          return GestureDetector(
            onTap: () { _history.switchSession(s.id); setState(() => _showSessions = false); },
            child: Container(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(color: act ? const Color(0xFF0071E3).withOpacity(0.1) : null),
              child: Row(children: [
                Icon(Icons.chat, size: 12, color: act ? const Color(0xFF0071E3) : Colors.white.withOpacity(0.3)),
                const SizedBox(width: 8),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(s.name, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: act ? const Color(0xFF0071E3) : Colors.white.withOpacity(0.6))),
                  Text(prev, style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3))),
                ])),
                GestureDetector(onTap: () { _history.deleteSession(s.id); setState(() {}); },
                  child: Icon(Icons.close, size: 12, color: Colors.white.withOpacity(0.2))),
              ])),
          );
        })),
      ]),
    );
  }

  Widget _dot3() => Padding(padding: const EdgeInsets.only(bottom: 4),
    child: Container(padding: const EdgeInsets.all(10), decoration: BoxDecoration(color: const Color(0xFF1C1C1E), borderRadius: BorderRadius.circular(16)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [0, 1, 2].map((i) => TweenAnimationBuilder(builder: (_, v, __) => Container(width: 5, height: 5, margin: const EdgeInsets.only(right: 2),
        decoration: BoxDecoration(shape: BoxShape.circle, color: const Color(0xFF00D4AA).withOpacity(v))), duration: Duration(milliseconds: 600 + i * 200), tween: Tween(begin: 0.3, end: 1.0))).toList())));
}
