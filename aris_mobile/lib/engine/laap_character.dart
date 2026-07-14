import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';

/// LAAP 角色引擎 — 从已有角色包加载
class LaapCharacter {
  final String name;
  final String displayName;
  final String source;
  final List<String> traits;
  final String speechStyle;
  final List<String> catchphrases;
  final List<String> likes;
  final List<String> dislikes;
  final String summary;
  final String vrmPath;

  LaapCharacter({
    required this.name,
    required this.displayName,
    this.source = '',
    this.traits = const [],
    this.speechStyle = '',
    this.catchphrases = const [],
    this.likes = const [],
    this.dislikes = const [],
    this.summary = '',
    this.vrmPath = '',
  });

  /// 从 LAAP 角色包 JSON 文件加载
  static Future<LaapCharacter> fromPackJson(String path) async {
    try {
      final file = File(path);
      final content = await file.readAsString();
      final data = jsonDecode(content) as Map<String, dynamic>;

      final personality = data['personality'] as Map<String, dynamic>? ?? {};
      final bio = data['biography'] as Map<String, dynamic>? ?? {};
      final traits = (personality['traits'] as List<dynamic>?)?.cast<String>() ?? [];
      final catchphrases = (personality['catchphrases'] as List<dynamic>?)?.cast<String>() ?? [];
      final likes = (personality['likes'] as List<dynamic>?)?.cast<String>() ?? [];
      final dislikes = (personality['dislikes'] as List<dynamic>?)?.cast<String>() ?? [];
      final sourceData = data['source'] as Map<String, dynamic>? ?? {};
      final vrmData = data['vrm_model'] as Map<String, dynamic>? ?? {};

      return LaapCharacter(
        name: data['character_name'] as String? ?? '',
        displayName: data['display_name'] as String? ?? '',
        source: sourceData['title'] as String? ?? '',
        traits: traits,
        speechStyle: personality['speech_style'] as String? ?? '',
        catchphrases: catchphrases,
        likes: likes,
        dislikes: dislikes,
        summary: bio['summary'] as String? ?? '',
        vrmPath: vrmData['path'] as String? ?? '',
      );
    } catch (e) {
      debugPrint('Failed to load character pack: $e');
      return LaapCharacter(name: 'Unknown', displayName: '未知');
    }
  }

  /// 获取所有可用角色的 packs 目录路径
  static String getPacksDir() {
    return r'D:\LAAP\laap\character_engine\packs';
  }

  /// 列出所有可用角色包
  static Future<List<String>> listAvailablePacks() async {
    final dir = Directory(getPacksDir());
    if (!await dir.exists()) return [];
    final files = await dir.list().where((e) => e.path.endsWith('.json')).toList();
    return files.map((e) => e.path).toList();
  }

  /// 加载所有角色
  static Future<List<LaapCharacter>> loadAll() async {
    final packs = await listAvailablePacks();
    final chars = <LaapCharacter>[];
    for (final pack in packs) {
      final char = await fromPackJson(pack);
      if (char.name.isNotEmpty) chars.add(char);
    }
    return chars;
  }

  /// 检查是否有对应的 Live2D 模型
  bool get hasLive2D => vrmPath.isNotEmpty;
}

/// LAAP Live2D 资源路径
class LaapLive2DPaths {
  static const baseDir = r'D:\LAAP\Live2D-Virtual-Girlfriend-main\Live2D-Virtual-Girlfriend-main\Character';

  /// 获取拉菲的 Live2D 模型路径
  static String get lafeiModel3 =>
      '$baseDir\\拉菲\\laffey Ⅱ\\Laffey Ⅱ.model3.json';
  static String get lafeiMoc3 =>
      '$baseDir\\拉菲\\laffey Ⅱ\\Laffey Ⅱ.moc3';
  static String get lafeiTexture =>
      '$baseDir\\拉菲\\laffey Ⅱ\\Laffey Ⅱ.4096\\texture_00.png';
  static String get lafeiPhysics =>
      '$baseDir\\拉菲\\laffey Ⅱ\\Laffey Ⅱ.physics3.json';
}
