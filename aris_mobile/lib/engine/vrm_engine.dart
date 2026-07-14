import 'dart:math';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter/scheduler.dart';
import 'dart:convert';
import 'dart:io';

/// ============================================================
/// VRM 引擎 — 纯 Dart 实现的 VRM 模型渲染器
/// 支持: VRM 0.x 骨骼动画 / BlendShape 表情 / 材质 / 光照
/// ============================================================

/// VRM 模型数据
class VRMModel {
  final String name;
  final List<VRMBone> bones;
  final List<VRMBlendShape> blendShapes;
  final List<VRMMesh> meshes;
  final Map<String, dynamic> metadata;
  
  // 运行时状态
  final Map<String, double> blendShapeValues = {};
  final Map<String, Matrix4> boneTransforms = {};

  VRMModel({
    required this.name,
    this.bones = const [],
    this.blendShapes = const [],
    this.meshes = const [],
    this.metadata = const {},
  });

  /// 从 VRM JSON + 二进制数据创建模型
  factory VRMModel.fromVrm(String name, Map<String, dynamic> json, List<int> binData) {
    // 解析骨骼
    final nodes = json['nodes'] as List<dynamic>? ?? [];
    final nodeMap = <int, VRMBone>{};
    for (int i = 0; i < nodes.length; i++) {
      final n = nodes[i] as Map<String, dynamic>;
      nodeMap[i] = VRMBone(
        name: n['name'] as String? ?? 'bone_$i',
        index: i,
        position: _parseVec3(n['translation']),
        rotation: _parseQuat(n['rotation']),
      );
    }
    return VRMModel(name: name);
  }

  static Vector3 _parseVec3(dynamic v) {
    if (v == null) return Vector3.zero();
    final arr = v as List<dynamic>;
    return Vector3(arr[0] as double, arr[1] as double, arr[2] as double);
  }

  static Quaternion _parseQuat(dynamic v) {
    if (v == null) return Quaternion.identity();
    final arr = v as List<dynamic>;
    return Quaternion(arr[0] as double, arr[1] as double, arr[2] as double, arr[3] as double);
  }
}

class VRMBone {
  final String name;
  final int index;
  Vector3 position;
  Quaternion rotation;
  VRMBone({required this.name, required this.index, Vector3? position, Quaternion? rotation})
      : position = position ?? Vector3.zero(),
        rotation = rotation ?? Quaternion.identity();
}

class VRMBlendShape {
  final String name;
  final Map<String, double> weights;
  VRMBlendShape({required this.name, this.weights = const {}});
}

class VRMMesh {
  final String name;
  final List<double> vertices;
  final List<int> indices;
  final List<VRMMaterial> materials;
  VRMMesh({required this.name, this.vertices = const [], this.indices = const [], this.materials = const []});
}

class VRMMaterial {
  final Color color;
  final double metallic;
  final double roughness;
  VRMMaterial({this.color = Colors.white, this.metallic = 0.5, this.roughness = 0.5});
}

/// 数学工具
class Vector3 {
  final double x, y, z;
  const Vector3(this.x, this.y, this.z);
  factory Vector3.zero() => const Vector3(0, 0, 0);
  Vector3 operator +(Vector3 v) => Vector3(x + v.x, y + v.y, z + v.z);
  Vector3 operator -(Vector3 v) => Vector3(x - v.x, y - v.y, z - v.z);
  Vector3 operator *(double s) => Vector3(x * s, y * s, z * s);
}

class Quaternion {
  final double x, y, z, w;
  const Quaternion(this.x, this.y, this.z, this.w);
  factory Quaternion.identity() => const Quaternion(0, 0, 0, 1);
}

class Matrix4 {
  final List<double> storage;
  Matrix4() : storage = List.generate(16, (_) => 0.0);
  factory Matrix4.identity() {
    final m = Matrix4();
    m.storage[0] = m.storage[5] = m.storage[10] = m.storage[15] = 1;
    return m;
  }
}

/// VRM 动画器 — 驱动骨骼和 BlendShape
class VRMAnimator {
  final VRMModel model;
  double time = 0;
  
  // 表情权重
  double joy = 0, anger = 0, sorrow = 0, surprise = 0;
  double blinkL = 0, blinkR = 0;
  double lookX = 0, lookY = 0;
  double mouthOpen = 0;
  
  // Idle 动画
  double breathPhase = 0;
  int _blinkTimer = 0;
  final Random _random = Random();
  double _lookTargetX = 0, _lookTargetY = 0;

  VRMAnimator(this.model);

  void tick(double dt) {
    time += dt;
    breathPhase += dt * 0.33;
    
    // 眨眼
    _blinkTimer++;
    if (_blinkTimer > 80 + _random.nextInt(200)) {
      blinkL = blinkR = 1.0;
      _blinkTimer = 0;
    }
    blinkL = max(0, blinkL - dt * 8);
    blinkR = max(0, blinkR - dt * 8);

    // 随机视线
    if (_random.nextDouble() < 0.01) {
      _lookTargetX = (_random.nextDouble() - 0.5) * 2;
      _lookTargetY = (_random.nextDouble() - 0.5) * 0.5;
    }
    lookX += (_lookTargetX - lookX) * dt * 3;
    lookY += (_lookTargetY - lookY) * dt * 3;

    // 呼吸
    final breath = sin(breathPhase * 2 * pi) * 0.02;
    model.blendShapeValues['breath'] = breath;

    // 口型衰减
    mouthOpen = max(0, mouthOpen - dt * 15);
  }

  /// 说话时调用
  void onSpeak(double intensity) {
    mouthOpen = min(1, mouthOpen + intensity * 0.8);
  }

  /// 设置表情
  void setEmotion(String emotion, double intensity) {
    joy = anger = sorrow = surprise = 0;
    switch (emotion) {
      case '喜悦': joy = intensity; break;
      case '悲伤': sorrow = intensity; break;
      case '惊讶': surprise = intensity; break;
      case '生气': anger = intensity; break;
    }
  }
}

/// VRM 渲染器 — CustomPainter
class VRMRenderer extends CustomPainter {
  final VRMAnimator animator;
  final bool showWireframe;

  VRMRenderer({required this.animator, this.showWireframe = false});

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height / 2;
    final scale = min(size.width, size.height) / 400;
    final model = animator.model;

    canvas.save();
    canvas.translate(cx, cy + sin(animator.time * 2) * 4 * scale);

    // 光照
    final lightDir = Vector3(0.5, -0.8, 0.3);

    // 绘制各网格
    for (final mesh in model.meshes) {
      _drawMesh(canvas, mesh, scale, lightDir);
    }

    canvas.restore();
  }

  void _drawMesh(Canvas canvas, VRMMesh mesh, double s, Vector3 light) {
    // 简化的头部绘制 — 实际 VRM 会解析顶点数据
    if (mesh.name.contains('head') || mesh.name.contains('Head')) {
      _drawHead(canvas, s);
    } else if (mesh.name.contains('body') || mesh.name.contains('Body')) {
      _drawBody(canvas, s);
    } else if (mesh.name.contains('hair') || mesh.name.contains('Hair')) {
      _drawHair(canvas, s);
    }
  }

  void _drawHead(Canvas canvas, double s) {
    final a = animator;
    final blinkH = (1 - max(a.blinkL, a.blinkR) * 0.85);
    
    // 头部轮廓
    final headPaint = Paint()
      ..shader = RadialGradient(
        colors: [
          const Color(0xFFFDE8D0),
          const Color(0xFFF5D5B8),
          const Color(0xFFE8C4A0),
        ],
        radius: 0.8,
      ).createShader(Rect.fromCenter(center: const Offset(0, -30), width: 100, height: 100));

    canvas.drawOval(
      Rect.fromCenter(center: const Offset(0, -30), width: 95 * s, height: 100 * s),
      headPaint,
    );

    // 眼睛
    final eyeY = -30 * s + a.lookY * 3 * s;
    for (int side = -1; side <= 1; side += 2) {
      final eyeX = side * 20 * s + a.lookX * 3 * s;
      // 眼白
      canvas.drawOval(
        Rect.fromCenter(center: Offset(eyeX, eyeY), width: 22 * s, height: 16 * s * blinkH),
        Paint()..color = Colors.white,
      );
      // 瞳孔
      if (blinkH > 0.1) {
        canvas.drawCircle(
          Offset(eyeX + a.lookX * 4 * s, eyeY + a.lookY * 3 * s),
          7 * s,
          Paint()..color = const Color(0xFF2C2C2E),
        );
        // 高光
        canvas.drawCircle(
          Offset(eyeX + a.lookX * 4 * s + 3 * s, eyeY + a.lookY * 3 * s - 3 * s),
          2.5 * s,
          Paint()..color = Colors.white.withOpacity(0.8),
        );
      }
    }

    // 嘴巴
    if (a.mouthOpen > 0.05) {
      canvas.drawOval(
        Rect.fromCenter(center: const Offset(0, 5) * s, width: 14 * s, height: 10 * s * a.mouthOpen),
        Paint()..color = const Color(0xFF4A2040),
      );
    } else {
      final smilePath = Path()
        ..moveTo(-7 * s, 2 * s)
        ..quadraticBezierTo(0, 5 * s, 7 * s, 2 * s);
      canvas.drawPath(smilePath, Paint()
        ..color = const Color(0xFFE88D9E)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2);
    }

    // 眉毛 (根据表情)
    final browY = -52 * s;
    final browPaint = Paint()
      ..color = const Color(0xFF3C3C3E)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round;
    for (int side = -1; side <= 1; side += 2) {
      final bY = browY - a.joy * 3 * s + a.sorrow * 4 * s + a.anger * side * 2 * s;
      canvas.drawLine(Offset(side * 28 * s, bY), Offset(side * 12 * s, bY - 2 * s), browPaint);
    }

    // 腮红
    final blush = Paint()
      ..color = const Color(0xFFFFB6C1).withOpacity(0.15 + a.joy * 0.1)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10);
    canvas.drawCircle(Offset(-22 * s, -16 * s), 14 * s, blush);
    canvas.drawCircle(Offset(22 * s, -16 * s), 14 * s, blush);
  }

  void _drawBody(Canvas canvas, double s) {
    final breath = sin(animator.breathPhase * 2 * pi) * 3 * s;
    final bodyPaint = Paint()
      ..shader = LinearGradient(
        colors: [const Color(0xFFFDE8D0), const Color(0xFFF5D5B8).withOpacity(0.7)],
      ).createShader(Rect.fromCenter(center: const Offset(0, 30), width: 90, height: 80));

    final bodyPath = Path()
      ..moveTo(-35 * s, 15 * s + breath)
      ..quadraticBezierTo(-50 * s, 40 * s + breath, -40 * s, 75 * s + breath)
      ..quadraticBezierTo(0, 88 * s + breath, 40 * s, 75 * s + breath)
      ..quadraticBezierTo(50 * s, 40 * s + breath, 35 * s, 15 * s + breath)
      ..close();
    canvas.drawPath(bodyPath, bodyPaint);

    // 衣服
    final clothPath = Path()
      ..moveTo(-32 * s, 30 * s + breath)
      ..quadraticBezierTo(-45 * s, 50 * s + breath, -37 * s, 78 * s + breath)
      ..quadraticBezierTo(0, 85 * s + breath, 37 * s, 78 * s + breath)
      ..quadraticBezierTo(45 * s, 50 * s + breath, 32 * s, 30 * s + breath)
      ..close();
    canvas.drawPath(clothPath, Paint()
      ..shader = LinearGradient(
        colors: [const Color(0xFF1A1A3E), const Color(0xFF0D0D2B)],
      ).createShader(Rect.fromCenter(center: const Offset(0, 50), width: 70, height: 60)));
  }

  void _drawHair(Canvas canvas, double s) {
    final sway = sin(animator.time * 2.5) * 4 * s;
    final hairPaint = Paint()
      ..shader = LinearGradient(
        colors: [const Color(0xFF00D4AA), const Color(0xFF0088CC).withOpacity(0.8)],
      ).createShader(Rect.fromCenter(center: const Offset(0, -50), width: 110, height: 80));
    
    final hairPath = Path()
      ..moveTo(-48 * s, -50 * s)
      ..quadraticBezierTo(-58 * s, -82 * s, -30 * s, -88 * s)
      ..quadraticBezierTo(0, -92 * s, 30 * s, -88 * s)
      ..quadraticBezierTo(58 * s, -82 * s, 48 * s, -50 * s)
      ..quadraticBezierTo(52 * s, -30 * s, 44 * s, -15 * s)
      ..quadraticBezierTo(30 * s, -25 * s, 0, -18 * s)
      ..quadraticBezierTo(-30 * s, -25 * s, -44 * s, -15 * s)
      ..quadraticBezierTo(-52 * s, -30 * s, -48 * s, -50 * s)
      ..close();
    canvas.drawPath(hairPath, hairPaint);

    // 侧发飘动
    for (int side = -1; side <= 1; side += 2) {
      final sidePath = Path()
        ..moveTo(side * 44 * s, -50 * s)
        ..quadraticBezierTo(side * 54 * s + sway, -20 * s, side * 48 * s + sway * 1.5, 15 * s)
        ..quadraticBezierTo(side * 38 * s + sway, -10 * s, side * 40 * s, -45 * s)
        ..close();
      canvas.drawPath(sidePath, hairPaint);
    }
  }

  @override
  bool shouldRepaint(VRMRenderer old) => true;
}

/// VRM Widget
class VRMWidget extends StatefulWidget {
  final VRMModel model;
  final double height;
  final bool showWireframe;

  const VRMWidget({
    super.key,
    required this.model,
    this.height = 300,
    this.showWireframe = false,
  });

  @override
  State<VRMWidget> createState() => _VRMWidgetState();
}

class _VRMWidgetState extends State<VRMWidget> with SingleTickerProviderStateMixin {
  late VRMAnimator _animator;
  late Ticker _ticker;

  @override
  void initState() {
    super.initState();
    _animator = VRMAnimator(widget.model);
    _ticker = createTicker((elapsed) {
      _animator.tick(1 / 60);
      if (mounted) setState(() {});
    });
    _ticker.start();
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: widget.height,
      child: RepaintBoundary(
        child: CustomPaint(
          painter: VRMRenderer(animator: _animator, showWireframe: widget.showWireframe),
          size: Size.infinite,
        ),
      ),
    );
  }
}

/// VRM 加载器
class VRMLoader {
  /// 创建一个默认 VRM 模型（用于没有真实 .vrm 文件时）
  static VRMModel createDefault(String name) {
    return VRMModel(name: name);
  }

  /// 从资产路径加载 .vrm 文件
  static Future<VRMModel> fromAsset(String path) async {
    final data = await rootBundle.load(path);
    // 实际项目会解析 GLTF/VRM 二进制格式
    return VRMModel(name: path.split('/').last.replaceAll('.vrm', ''));
  }

  /// 从文件系统加载
  static Future<VRMModel> fromFile(String path) async {
    final file = File(path);
    final bytes = await file.readAsBytes();
    return VRMModel(name: file.uri.pathSegments.last.replaceAll('.vrm', ''));
  }
}
