import 'dart:math';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

/// Live2D 风格角色渲染引擎 — 用 Canvas 绘制高质量Live2D风格动画
/// 支持：呼吸、眨眼、头发飘动、口型同步、身体晃动、自定义导入
class Live2DRenderer extends CustomPainter {
  final Live2DCharacter char;
  final double time;
  final double breathPhase;
  final bool isTalking;
  final double blinkState; // 0=open, 0-1=closing, 1=closed
  final double lookTargetX; // -1 to 1
  final double lookTargetY; // -1 to 1

  Live2DRenderer({
    required this.char,
    required this.time,
    this.breathPhase = 0,
    this.isTalking = false,
    this.blinkState = 0,
    this.lookTargetX = 0,
    this.lookTargetY = 0,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height / 2;
    final scale = min(size.width, size.height) / 400;

    final breath = sin(breathPhase * 2 * pi) * 3 * scale;
    final headBob = sin(breathPhase * 2 * pi) * 1.5 * scale;
    final floatY = sin(time * 2) * 4 * scale;

    canvas.save();
    canvas.translate(cx, cy + floatY);

    _drawShadow(canvas, scale);
    _drawBody(canvas, scale, breath);
    _drawHead(canvas, scale, breath, headBob);
    _drawHair(canvas, scale, time);
    _drawEyes(canvas, scale);
    _drawEyebrows(canvas, scale);
    _drawMouth(canvas, scale);
    _drawBlush(canvas, scale);
    _drawAccessories(canvas, scale, time);

    canvas.restore();
  }

  void _drawShadow(Canvas canvas, double s) {
    final paint = Paint()
      ..color = Colors.black.withOpacity(0.08)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 20);
    canvas.drawOval(Rect.fromCenter(
      center: const Offset(0, 90),
      width: 120 * s,
      height: 20 * s,
    ), paint);
  }

  void _drawBody(Canvas canvas, double s, double breath) {
    // 肩膀
    final bodyPaint = Paint()
      ..shader = LinearGradient(
        colors: [
          char.skinColor.withOpacity(0.9),
          char.skinColor.withOpacity(0.7),
        ],
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
      ).createShader(Rect.fromCenter(center: const Offset(0, 30), width: 100 * s, height: 80 * s));

    // 身体
    final bodyPath = Path();
    bodyPath.moveTo(-30 * s, 10 * s + breath);
    bodyPath.quadraticBezierTo(
      -45 * s, 30 * s + breath,
      -35 * s, 70 * s + breath,
    );
    bodyPath.quadraticBezierTo(
      0, 85 * s + breath,
      35 * s, 70 * s + breath,
    );
    bodyPath.quadraticBezierTo(
      45 * s, 30 * s + breath,
      30 * s, 10 * s + breath,
    );
    bodyPath.close();
    canvas.drawPath(bodyPath, bodyPaint);

    // 衣服 (根据角色配色)
    final clothColor = char.clothColor ?? char.accentColor;
    final clothPaint = Paint()
      ..shader = LinearGradient(
        colors: [clothColor, clothColor.withOpacity(0.6)],
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
      ).createShader(Rect.fromCenter(center: const Offset(0, 45), width: 70 * s, height: 60 * s));

    final clothPath = Path();
    clothPath.moveTo(-28 * s, 25 * s + breath);
    clothPath.quadraticBezierTo(
      -40 * s, 45 * s + breath,
      -32 * s, 75 * s + breath,
    );
    clothPath.quadraticBezierTo(
      0, 82 * s + breath,
      32 * s, 75 * s + breath,
    );
    clothPath.quadraticBezierTo(
      40 * s, 45 * s + breath,
      28 * s, 25 * s + breath,
    );
    clothPath.close();
    canvas.drawPath(clothPath, clothPaint);
  }

  void _drawHead(Canvas canvas, double s, double breath, double bob) {
    // 头部 — 使用角色肤色
    final headPaint = Paint()
      ..shader = RadialGradient(
        colors: [
          char.skinColor,
          char.skinColor.withOpacity(0.85),
          char.skinColor.withOpacity(0.7),
        ],
        radius: 0.8,
      ).createShader(Rect.fromCenter(center: Offset(0, -30 * s + bob), width: 90 * s, height: 90 * s));

    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(0, -30 * s + bob),
        width: 90 * s,
        height: 95 * s,
      ),
      headPaint,
    );

    // 下巴
    final jawPaint = Paint()
      ..shader = RadialGradient(
        colors: [
          char.skinColor.withOpacity(0.5),
          char.skinColor.withOpacity(0.2),
          Colors.transparent,
        ],
      ).createShader(Rect.fromCenter(center: Offset(0, 10 * s + bob), width: 50 * s, height: 30 * s));

    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(0, 10 * s + bob),
        width: 50 * s,
        height: 25 * s,
      ),
      jawPaint,
    );
  }

  void _drawHair(Canvas canvas, double s, double t) {
    // 头发 — 使用角色主色
    final hairColor = char.hairColor ?? char.accentColor;
    final hairPaint = Paint()
      ..shader = LinearGradient(
        colors: [hairColor, hairColor.withOpacity(0.8)],
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
      ).createShader(Rect.fromCenter(center: const Offset(0, -50), width: 110 * s, height: 80 * s));

    // 头发主体
    final hairPath = Path();
    hairPath.moveTo(-45 * s, -50 * s);
    hairPath.quadraticBezierTo(-55 * s, -80 * s, -30 * s, -85 * s);
    hairPath.quadraticBezierTo(0, -90 * s, 30 * s, -85 * s);
    hairPath.quadraticBezierTo(55 * s, -80 * s, 45 * s, -50 * s);
    hairPath.quadraticBezierTo(50 * s, -30 * s, 42 * s, -15 * s);
    hairPath.quadraticBezierTo(30 * s, -25 * s, 20 * s, -20 * s);
    hairPath.quadraticBezierTo(0, -15 * s, -20 * s, -20 * s);
    hairPath.quadraticBezierTo(-30 * s, -25 * s, -42 * s, -15 * s);
    hairPath.quadraticBezierTo(-50 * s, -30 * s, -45 * s, -50 * s);
    hairPath.close();
    canvas.drawPath(hairPath, hairPaint);

    // 刘海
    final bangsPaint = Paint()
      ..shader = LinearGradient(
        colors: [hairColor, hairColor.withOpacity(0.7)],
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
      ).createShader(Rect.fromCenter(center: const Offset(0, -55), width: 80 * s, height: 40 * s));

    final bangsPath = Path();
    bangsPath.moveTo(-40 * s, -50 * s);
    bangsPath.quadraticBezierTo(-35 * s, -35 * s, -20 * s, -38 * s);
    bangsPath.quadraticBezierTo(0, -40 * s, 20 * s, -38 * s);
    bangsPath.quadraticBezierTo(35 * s, -35 * s, 40 * s, -50 * s);
    bangsPath.quadraticBezierTo(45 * s, -60 * s, 40 * s, -75 * s);
    bangsPath.quadraticBezierTo(0, -80 * s, -40 * s, -75 * s);
    bangsPath.quadraticBezierTo(-45 * s, -60 * s, -40 * s, -50 * s);
    bangsPath.close();
    canvas.drawPath(bangsPath, bangsPaint);

    // 侧发飘动
    for (int side = -1; side <= 1; side += 2) {
      final sway = sin(t * 2.5 + side) * 5 * s;
      final sideHairPaint = Paint()
        ..shader = LinearGradient(
          colors: [hairColor, hairColor.withOpacity(0.6)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ).createShader(Rect.fromCenter(
          center: Offset(side * 40 * s + sway, -20 * s),
          width: 20 * s,
          height: 60 * s,
        ));

      final sidePath = Path();
      sidePath.moveTo(side * 42 * s, -50 * s);
      sidePath.quadraticBezierTo(
        side * 50 * s + sway, -20 * s,
        side * 45 * s + sway * 1.5, 10 * s,
      );
      sidePath.quadraticBezierTo(
        side * 35 * s + sway, -10 * s,
        side * 38 * s, -45 * s,
      );
      sidePath.close();
      canvas.drawPath(sidePath, sideHairPaint);
    }
  }

  void _drawEyes(Canvas canvas, double s) {
    // 左眼
    _drawEye(canvas, -18 * s, -32 * s, s, true);
    // 右眼
    _drawEye(canvas, 18 * s, -32 * s, s, false);
  }

  void _drawEye(Canvas canvas, double x, double y, double s, bool isLeft) {
    // 眼白
    final whitePaint = Paint()..color = Colors.white;
    final eyeW = 20 * s;
    final eyeH = 14 * s * (1 - blinkState * 0.8);

    canvas.drawOval(
      Rect.fromCenter(center: Offset(x, y), width: eyeW, height: max(2, eyeH)),
      whitePaint,
    );

    if (blinkState < 0.8) {
      // 瞳孔
      final lookX = lookTargetX * 4 * s;
      final lookY = lookTargetY * 3 * s;
      final pupilPaint = Paint()..color = char.eyeColor ?? const Color(0xFF2C2C2E);

      canvas.drawCircle(
        Offset(x + lookX, y + lookY),
        7 * s,
        pupilPaint,
      );

      // 高光
      final highlightPaint = Paint()..color = Colors.white.withOpacity(0.8);
      canvas.drawCircle(
        Offset(x + lookX + 3 * s, y + lookY - 3 * s),
        2.5 * s,
        highlightPaint,
      );
    }

    // 眼线
    final linePaint = Paint()
      ..color = const Color(0xFF2C2C2E)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    canvas.drawOval(
      Rect.fromCenter(center: Offset(x, y), width: eyeW, height: max(2, eyeH)),
      linePaint,
    );
  }

  void _drawEyebrows(Canvas canvas, double s) {
    final browPaint = Paint()
      ..color = const Color(0xFF3C3C3E)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round;

    for (int side = -1; side <= 1; side += 2) {
      final browY = -48 * s + (isTalking ? -2 * s : 0.0);
      canvas.drawLine(
        Offset(side * 28 * s, browY),
        Offset(side * 10 * s, browY - 3 * s),
        browPaint,
      );
    }
  }

  void _drawMouth(Canvas canvas, double s) {
    final mouthOpen = isTalking ? 0.3 + sin(time * 20) * 0.3 : 0;

    if (mouthOpen > 0.1) {
      // 张嘴
      final mouthPaint = Paint()
        ..color = const Color(0xFF4A2040);
      canvas.drawOval(
        Rect.fromCenter(
          center: Offset(0, -8 * s),
          width: 12 * s,
          height: 8 * s * mouthOpen,
        ),
        mouthPaint,
      );

      // 舌头
      if (mouthOpen > 0.3) {
        final tonguePaint = Paint()
          ..color = const Color(0xFFE88D9E);
        canvas.drawOval(
          Rect.fromCenter(
            center: Offset(0, -6 * s),
            width: 8 * s,
            height: 4 * s * mouthOpen,
          ),
          tonguePaint,
        );
      }
    } else {
      // 闭嘴 - 微笑
      final smilePaint = Paint()
        ..color = const Color(0xFFE88D9E)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2;

      final smilePath = Path();
      smilePath.moveTo(-6 * s, -5 * s);
      smilePath.quadraticBezierTo(0, -2 * s, 6 * s, -5 * s);
      canvas.drawPath(smilePath, smilePaint);
    }
  }

  void _drawBlush(Canvas canvas, double s) {
    final blushPaint = Paint()
      ..color = const Color(0xFFFFB6C1).withOpacity(0.2)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8);

    canvas.drawCircle(Offset(-22 * s, -18 * s), 12 * s, blushPaint);
    canvas.drawCircle(Offset(22 * s, -18 * s), 12 * s, blushPaint);
  }

  void _drawAccessories(Canvas canvas, double s, double t) {
    // 角色饰品光效
    if (char.hasAccessory) {
      final glowPaint = Paint()
        ..color = char.accentColor.withOpacity(0.15 + sin(t * 3) * 0.05)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 15);

      canvas.drawCircle(Offset(0, -75 * s), 20 * s, glowPaint);

      // 头顶光点
      final dotPaint = Paint()
        ..color = char.accentColor.withOpacity(0.6 + sin(t * 4) * 0.2);
      canvas.drawCircle(Offset(0, -78 * s), 3 * s, dotPaint);
    }
  }

  @override
  bool shouldRepaint(Live2DRenderer old) => true;
}

/// Live2D 角色数据 — 可自定义导入
class Live2DCharacter {
  final String name;
  final Color skinColor;
  final Color accentColor;
  final Color? hairColor;
  final Color? eyeColor;
  final Color? clothColor;
  final bool hasAccessory;

  const Live2DCharacter({
    required this.name,
    this.skinColor = const Color(0xFFFDE8D0),
    this.accentColor = const Color(0xFF00D4AA),
    this.hairColor,
    this.eyeColor,
    this.clothColor,
    this.hasAccessory = true,
  });

  // 预设角色
  static const aris = Live2DCharacter(
    name: 'Aris',
    skinColor: Color(0xFFFDE8D0),
    accentColor: Color(0xFF00D4AA),
    hairColor: Color(0xFF00D4AA),
    eyeColor: Color(0xFF0088CC),
    clothColor: Color(0xFF1A1A3E),
  );

  static const tianlangxing = Live2DCharacter(
    name: '天狼星',
    skinColor: Color(0xFFFFF0F5),
    accentColor: Color(0xFFFF69B4),
    hairColor: Color(0xFFFFB6C1),
    eyeColor: Color(0xFF9370DB),
    clothColor: Color(0xFFFF69B4),
  );

  static const lafei = Live2DCharacter(
    name: '拉菲',
    skinColor: Color(0xFFF0F8FF),
    accentColor: Color(0xFF87CEEB),
    hairColor: Color(0xFF4169E1),
    eyeColor: Color(0xFF1E90FF),
    clothColor: Color(0xFF87CEEB),
  );

  static const enterprise = Live2DCharacter(
    name: '企业',
    skinColor: Color(0xFFF5F5F5),
    accentColor: Color(0xFFC0C0C0),
    hairColor: Color(0xFF708090),
    eyeColor: Color(0xFF4682B4),
    clothColor: Color(0xFF2F4F4F),
  );

  static const kewei = Live2DCharacter(
    name: '可畏',
    skinColor: Color(0xFFFFE4E1),
    accentColor: Color(0xFF9370DB),
    hairColor: Color(0xFF6A5ACD),
    eyeColor: Color(0xFF8A2BE2),
    clothColor: Color(0xFF9370DB),
  );

  static const List<Live2DCharacter> defaults = [
    aris, tianlangxing, lafei, enterprise, kewei,
  ];
}

/// Live2D 动画控制器
class Live2DAnimator {
  double time = 0;
  double breathPhase = 0;
  double blinkState = 0;
  bool isTalking = false;
  double lookTargetX = 0;
  double lookTargetY = 0;
  int _blinkTimer = 0;
  final Random _random = Random();

  void tick(double dt) {
    time += dt;
    breathPhase += dt * 0.33;

    // 眨眼
    _blinkTimer++;
    if (_blinkTimer > 120 + _random.nextInt(180)) {
      // 闭眼 0.1s
      blinkState = 1.0;
      _blinkTimer = 0;
    }
    if (blinkState > 0) {
      blinkState = (blinkState - dt * 10).clamp(0, 1);
    }

    // 随机视线
    lookTargetX += (_random.nextDouble() - 0.5) * dt * 2;
    lookTargetY += (_random.nextDouble() - 0.5) * dt * 2;
    lookTargetX = lookTargetX.clamp(-1, 1);
    lookTargetY = lookTargetY.clamp(-1, 1);
  }

  Live2DRenderer createRenderer(Live2DCharacter char) {
    return Live2DRenderer(
      char: char,
      time: time,
      breathPhase: breathPhase,
      isTalking: isTalking,
      blinkState: blinkState,
      lookTargetX: lookTargetX,
      lookTargetY: lookTargetY,
    );
  }
}

/// Live2D 显示 Widget
class Live2DWidget extends StatefulWidget {
  final Live2DCharacter character;
  final double height;
  final bool isTalking;

  const Live2DWidget({
    super.key,
    this.character = Live2DCharacter.aris,
    this.height = 300,
    this.isTalking = false,
  });

  @override
  State<Live2DWidget> createState() => _Live2DWidgetState();
}

class _Live2DWidgetState extends State<Live2DWidget>
    with SingleTickerProviderStateMixin {
  late final Live2DAnimator _animator;
  late Ticker _ticker;

  @override
  void initState() {
    super.initState();
    _animator = Live2DAnimator();
    _ticker = createTicker((elapsed) {
      _animator.isTalking = widget.isTalking;
      _animator.tick(1 / 60);
      if (mounted) setState(() {});
    });
    _ticker.start();
  }

  @override
  void didUpdateWidget(Live2DWidget old) {
    super.didUpdateWidget(old);
    _animator.isTalking = widget.isTalking;
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
          painter: _animator.createRenderer(widget.character),
          size: Size.infinite,
        ),
      ),
    );
  }
}
