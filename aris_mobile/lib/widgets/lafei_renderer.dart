import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

/// 拉菲 Live2D 风格角色渲染 — 纯 Canvas，不用 WebView
class LafeiRenderer extends CustomPainter {
  final double time;
  final double mouthOpen; // 0-1
  final double blink;     // 0=开, 1=闭
  final String expression; // normal, smile, angry

  LafeiRenderer({this.time = 0, this.mouthOpen = 0, this.blink = 0, this.expression = 'normal'});

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2, cy = size.height / 2;
    final s = min(size.width, size.height) / 380;
    final breath = sin(time * 2.5) * 2 * s;
    final bob = sin(time * 1.8) * 3 * s;

    canvas.save();
    canvas.translate(cx, cy + bob);

    // 阴影
    _shadow(canvas, s);
    // 头发 (浅蓝色)
    _hair(canvas, s, time);
    // 头部
    _head(canvas, s, breath);
    // 眼睛 (大眼风格)
    _eyes(canvas, s);
    // 嘴巴
    _mouth(canvas, s);
    // 腮红
    _blush(canvas, s);
    // 身体
    _body(canvas, s, breath);
    // 衣服 (拉菲风格)
    _clothes(canvas, s, breath);
    // 蝴蝶结
    _ribbon(canvas, s, time);

    canvas.restore();
  }

  void _shadow(Canvas c, double s) {
    final p = Paint()..color = Colors.black.withOpacity(0.06)..maskFilter = const MaskFilter.blur(BlurStyle.normal, 15);
    c.drawOval(Rect.fromCenter(center: const Offset(0, 75), width: 100 * s, height: 16 * s), p);
  }

  void _head(Canvas c, double s, double b) {
    final p = Paint()..shader = RadialGradient(colors: [
      const Color(0xFFFFF5EE), const Color(0xFFFFE8D0), const Color(0xFFFFDCC0),
    ]).createShader(Rect.fromCenter(center: Offset(0, -25 * s), width: 85 * s, height: 90 * s));
    c.drawOval(Rect.fromCenter(center: Offset(0, -25 * s + b), width: 85 * s, height: 92 * s), p);
  }

  void _hair(Canvas c, double s, double t) {
    final hairColor = const Color(0xFF87CEEB);
    final darkHair = const Color(0xFF6BB3D9);
    final sway = sin(t * 2.2) * 3 * s;
    
    // 后发
    Paint p = Paint()..shader = LinearGradient(colors: [darkHair, hairColor]).createShader(Rect.fromCenter(center: const Offset(0, -45), width: 100 * s, height: 70 * s));
    Path path = Path();
    path.moveTo(-42 * s, -45 * s);
    path.quadraticBezierTo(-52 * s, -75 * s, -28 * s, -82 * s);
    path.quadraticBezierTo(0, -85 * s, 28 * s, -82 * s);
    path.quadraticBezierTo(52 * s, -75 * s, 42 * s, -45 * s);
    path.quadraticBezierTo(46 * s, -25 * s, 40 * s, -10 * s);
    path.quadraticBezierTo(28 * s, -20 * s, 20 * s, -18 * s);
    path.quadraticBezierTo(0, -15 * s, -20 * s, -18 * s);
    path.quadraticBezierTo(-28 * s, -20 * s, -40 * s, -10 * s);
    path.quadraticBezierTo(-46 * s, -25 * s, -42 * s, -45 * s);
    path.close();
    c.drawPath(path, p);
    
    // 刘海
    p = Paint()..shader = LinearGradient(colors: [hairColor, darkHair]).createShader(Rect.fromCenter(center: const Offset(0, -50), width: 75 * s, height: 35 * s));
    path = Path();
    path.moveTo(-38 * s, -45 * s);
    path.quadraticBezierTo(-34 * s, -28 * s, -18 * s, -32 * s);
    path.quadraticBezierTo(0, -34 * s, 18 * s, -32 * s);
    path.quadraticBezierTo(34 * s, -28 * s, 38 * s, -45 * s);
    path.quadraticBezierTo(42 * s, -55 * s, 38 * s, -70 * s);
    path.quadraticBezierTo(0, -75 * s, -38 * s, -70 * s);
    path.close();
    c.drawPath(path, p);

    // 侧发飘动
    for (int side = -1; side <= 1; side += 2) {
      p = Paint()..shader = LinearGradient(colors: [hairColor, darkHair.withOpacity(0.6)]).createShader(Rect.fromCenter(center: Offset(side * 38 * s + sway, -18 * s), width: 18 * s, height: 55 * s));
      path = Path();
      path.moveTo(side * 40 * s, -45 * s);
      path.quadraticBezierTo(side * 48 * s + sway, -18 * s, side * 42 * s + sway * 1.5, 10 * s);
      path.quadraticBezierTo(side * 34 * s + sway, -8 * s, side * 35 * s, -40 * s);
      path.close();
      c.drawPath(path, p);
    }
  }

  void _eyes(Canvas c, double s) {
    final blinkH = 1 - blink * 0.85;
    final eyeY = -24 * s;
    
    for (int side = -1; side <= 1; side += 2) {
      final ex = side * 20 * s;
      // 眼白
      c.drawOval(Rect.fromCenter(center: Offset(ex, eyeY), width: 24 * s, height: 18 * s * blinkH), Paint()..color = Colors.white);
      if (blink < 0.8) {
        // 瞳孔 (拉菲的蓝色大眼)
        c.drawCircle(Offset(ex + side * 2 * s, eyeY + 1 * s), 8 * s, Paint()..color = const Color(0xFF4169E1));
        c.drawCircle(Offset(ex + side * 1 * s, eyeY - 1 * s), 4 * s, Paint()..color = const Color(0xFF1E90FF));
        // 高光
        c.drawCircle(Offset(ex + side * 2 * s, eyeY - 3 * s), 3 * s, Paint()..color = Colors.white.withOpacity(0.9));
        c.drawCircle(Offset(ex + side * 3 * s, eyeY + 2 * s), 1.5 * s, Paint()..color = Colors.white.withOpacity(0.6));
      }
      // 眼线
      c.drawOval(Rect.fromCenter(center: Offset(ex, eyeY), width: 24 * s, height: 18 * s * blinkH), Paint()..color = const Color(0xFF2C2C2E)..style = PaintingStyle.stroke..strokeWidth = 1.5);
    }
  }

  void _mouth(Canvas c, double s) {
    if (mouthOpen > 0.05) {
      c.drawOval(Rect.fromCenter(center: const Offset(0, -5) * s, width: 12 * s, height: 8 * s * mouthOpen), Paint()..color = const Color(0xFF4A2040));
      if (mouthOpen > 0.3) c.drawOval(Rect.fromCenter(center: const Offset(0, -3) * s, width: 7 * s, height: 3 * s * mouthOpen), Paint()..color = const Color(0xFFE88D9E));
    } else {
      final smile = Path()..moveTo(-6 * s, -3 * s)..quadraticBezierTo(0, 0 * s, 6 * s, -3 * s);
      c.drawPath(smile, Paint()..color = const Color(0xFFE88D9E)..style = PaintingStyle.stroke..strokeWidth = 2);
    }
  }

  void _blush(Canvas c, double s) {
    final p = Paint()..color = const Color(0xFFFFB6C1).withOpacity(0.15)..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8);
    c.drawCircle(Offset(-20 * s, -14 * s), 12 * s, p);
    c.drawCircle(Offset(20 * s, -14 * s), 12 * s, p);
  }

  void _body(Canvas c, double s, double b) {
    final bodyPaint = Paint()..shader = LinearGradient(colors: [const Color(0xFFFFF5EE), const Color(0xFFFFE8D0).withOpacity(0.7)])
      .createShader(Rect.fromCenter(center: const Offset(0, 25), width: 80 * s, height: 70 * s));
    final bodyPath = Path()
      ..moveTo(-30 * s, 10 * s + b)
      ..quadraticBezierTo(-42 * s, 30 * s + b, -35 * s, 65 * s + b)
      ..quadraticBezierTo(0, 75 * s + b, 35 * s, 65 * s + b)
      ..quadraticBezierTo(42 * s, 30 * s + b, 30 * s, 10 * s + b)..close();
    c.drawPath(bodyPath, bodyPaint);
  }

  void _clothes(Canvas c, double s, double b) {
    // 海军领 (白+蓝色)
    final clothPaint = Paint()..shader = LinearGradient(colors: [const Color(0xFFFFFFFF), const Color(0xFFE8F4FD)])
      .createShader(Rect.fromCenter(center: const Offset(0, 40), width: 60 * s, height: 50 * s));
    final clothPath = Path()
      ..moveTo(-28 * s, 22 * s + b)
      ..quadraticBezierTo(-38 * s, 40 * s + b, -32 * s, 68 * s + b)
      ..quadraticBezierTo(0, 74 * s + b, 32 * s, 68 * s + b)
      ..quadraticBezierTo(38 * s, 40 * s + b, 28 * s, 22 * s + b)..close();
    c.drawPath(clothPath, clothPaint);

    // 领带/蝴蝶结
    final tiePaint = Paint()..color = const Color(0xFF4169E1);
    c.drawRect(Rect.fromCenter(center: Offset(0, 30 * s + b), width: 8 * s, height: 20 * s), tiePaint);
  }

  void _ribbon(Canvas c, double s, double t) {
    // 发饰
    final glow = 0.3 + sin(t * 3) * 0.1;
    final p = Paint()..color = const Color(0xFFFF69B4).withOpacity(glow);
    c.drawCircle(Offset(0, -72 * s), 6 * s, p);
    // 右蝴蝶结
    c.drawOval(Rect.fromCenter(center: Offset(10 * s, -72 * s), width: 12 * s, height: 6 * s), Paint()..color = const Color(0xFFFF69B4));
    c.drawOval(Rect.fromCenter(center: Offset(-10 * s, -72 * s), width: 12 * s, height: 6 * s), Paint()..color = const Color(0xFFFF69B4));
  }

  @override
  bool shouldRepaint(LafeiRenderer old) => true;
}

/// 拉菲 Live2D Widget
class LafeiWidget extends StatefulWidget {
  final double height;
  final bool isTalking;
  const LafeiWidget({super.key, this.height = 200, this.isTalking = false});

  @override
  State<LafeiWidget> createState() => LafeiWidgetState();
}

class LafeiWidgetState extends State<LafeiWidget> with SingleTickerProviderStateMixin {
  double _time = 0;
  double _mouth = 0;
  double _blink = 0;
  int _blinkTimer = 0;
  late Ticker _ticker;
  final Random _r = Random();

  @override
  void initState() {
    super.initState();
    _ticker = createTicker((elapsed) {
      _time += 1 / 60;
      // 口型
      _mouth += ((widget.isTalking ? 0.4 + sin(_time * 18) * 0.3 : 0) - _mouth) * 0.15;
      // 眨眼
      _blinkTimer++;
      if (_blinkTimer > 80 + _r.nextInt(200)) { _blink = 1; _blinkTimer = 0; }
      _blink = (_blink - (1 / 60) * 8).clamp(0, 1);
      if (mounted) setState(() {});
    });
    _ticker.start();
  }

  @override
  void dispose() { _ticker.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: widget.height,
      child: RepaintBoundary(
        child: CustomPaint(
          painter: LafeiRenderer(time: _time, mouthOpen: _mouth, blink: _blink),
          size: Size.infinite,
        ),
      ),
    );
  }
  
  void setSpeaking(double v) {}  // 由外部 ticker 控制
  void setSilent() {}
}
