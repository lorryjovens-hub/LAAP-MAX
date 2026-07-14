import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// PC 指令执行服务 — 手机发送指令让 PC 干活
class PCCommandService {
  String _pcIp = '192.168.1.100';
  static const _port = 11525;
  bool _connected = false;

  bool get isConnected => _connected;

  Future<void> init() async {
    final p = await SharedPreferences.getInstance();
    _pcIp = p.getString('pc_ip') ?? '192.168.1.100';
  }

  Future<bool> connect() async {
    try {
      final r = await http.get(Uri.parse('http://$_pcIp:$_port/mobile/ping')).timeout(const Duration(seconds: 3));
      _connected = r.statusCode == 200;
      return _connected;
    } catch (_) {
      _connected = false;
      return false;
    }
  }

  /// 执行 PC 指令
  Future<String> execute(String command) async {
    try {
      final r = await http.post(
        Uri.parse('http://$_pcIp:$_port/mobile/command'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'cmd': command, 'device': 'aris-mobile'}),
      ).timeout(const Duration(seconds: 30));
      if (r.statusCode == 200) {
        final d = jsonDecode(r.body);
        return d['result'] as String? ?? d['output'] as String? ?? '执行成功';
      }
      return 'PC 返回: ${r.statusCode}';
    } catch (e) {
      return 'PC 连接失败: $e';
    }
  }

  /// 文件操作
  Future<String> readFile(String path) => execute('read_file $path');
  Future<String> runScript(String script) => execute('run $script');
  Future<String> runCommand(String cmd) => execute('cmd $cmd');
}
