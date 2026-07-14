import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter/webview_flutter.dart';

/// Live2D WebView Widget — 用 Cubism.js 渲染拉菲 Live2D 模型
class Live2DWidget extends StatefulWidget {
  final double height;
  const Live2DWidget({super.key, this.height = 200});

  @override
  State<Live2DWidget> createState() => Live2DWidgetState();
}

class Live2DWidgetState extends State<Live2DWidget> {
  WebViewController? _ctrl;
  bool _loaded = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    _ctrl = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0x00000000))
      ..setNavigationDelegate(NavigationDelegate(
        onPageFinished: (_) => _loaded = true,
        onWebResourceError: (e) => setState(() => _error = e.description),
      ));

    // 通过 JavaScript 注入所有资源
    final html = await _buildHtml();
    await _ctrl!.loadHtmlString(html);
  }

  Future<String> _buildHtml() async {
    // 从 AssetBundle 读取所有 JS core 文件
    final pixiJs = await rootBundle.loadString('assets/live2d/core/pixi.min.js');
    final live2dJs = await rootBundle.loadString('assets/live2d/core/live2d.min.js');
    final cubismJs = await rootBundle.loadString('assets/live2d/core/live2dcubismcore.min.js');

    // 读取模型文件(base64编码)
    final mocBytes = (await rootBundle.load('assets/live2d/models/lafei/Laffey 2.moc3')).buffer.asUint8List();
    final mocB64 = base64Encode(mocBytes);

    final texBytes = (await rootBundle.load('assets/live2d/models/lafei/Laffey 2.4096/texture_00.png')).buffer.asUint8List();
    final texB64 = base64Encode(texBytes);

    final modelJson = await rootBundle.loadString('assets/live2d/models/lafei/Laffey 2.model3.json');

    return '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>*{margin:0;padding:0}html,body{width:100%;height:100%;overflow:hidden;background:transparent}#c{width:100%;height:100%}</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
// ===== 注入 JS Core =====
$pixiJs
$live2dJs
$cubismJs

// ===== 模型数据 (Base64) =====
const MOC_B64 = "$mocB64";
const TEX_B64 = "$texB64";
const MODEL_JSON = $modelJson;

// ===== 初始化 =====
let app, model, mouthOpen=0, targetMouth=0, blinkL=0, blinkR=0, bp=0;

async function init(){
  try{
    // PIXI App
    app = new PIXI.Application({
      view: document.getElementById('c'),
      width: window.innerWidth,
      height: window.innerHeight,
      transparent: true,
      antialias: true,
      resolution: Math.min(window.devicePixelRatio||1, 2),
      autoDensity: true,
    });

    // 加载贴图
    const texImg = new Image();
    texImg.src = 'data:image/png;base64,' + TEX_B64;
    await new Promise(r => { texImg.onload = r; });

    // 加载 MOC3
    const binStr = atob(MOC_B64);
    const bytes = new Uint8Array(binStr.length);
    for (let i = 0; i < binStr.length; i++) bytes[i] = binStr.charCodeAt(i);
    const coreModel = Live2DCubismCore.Model.fromArrayBuffer(bytes.buffer);
    
    // 创建 Live2D 模型
    model = new PIXI.live2d.Live2DModel(coreModel, { autoInteract: false });
    
    // 设置贴图
    if (model.internalModel.textures[0]) {
      model.internalModel.textures[0] = PIXI.Texture.from(texImg);
    }

    // 缩放
    const s = Math.min(window.innerWidth / 500, window.innerHeight / 600);
    model.scale.set(s);
    model.position.set(window.innerWidth / 2, window.innerHeight * 0.85);
    app.stage.addChild(model);

    // 动画
    app.ticker.add(animate);
    
    // 通知 Flutter
    try { Live2DLoaded.postMessage('ok'); } catch(e) {}
  } catch(e) {
    console.error('Live2D init error:', e);
    try { Live2DError.postMessage(e.message); } catch(ex) {}
  }
}

function animate() {
  if (!model || !model.internalModel) return;
  const p = model.internalModel.parameterValues;
  const ids = model.internalModel.parameterIds;
  
  mouthOpen += (targetMouth - mouthOpen) * 0.15;
  bp += 0.033;
  blinkL += (blinkL > 0.5 ? -0.15 : 0);
  blinkR += (blinkR > 0.5 ? -0.15 : 0);

  for (let i = 0; i < ids.length; i++) {
    const id = ids[i];
    if (id === 'ParamMouthOpenY') p[i] = mouthOpen * 0.7;
    else if (id === 'ParamEyeLOpen') p[i] = 1 - blinkL * 0.85;
    else if (id === 'ParamEyeROpen') p[i] = 1 - blinkR * 0.85;
    else if (id === 'ParamBreath') p[i] = Math.sin(bp * 2 * Math.PI) * 0.03;
  }
}

// 随机眨眼
setInterval(() => {
  if (Math.random() < 0.04) {
    blinkL = blinkR = 1;
    setTimeout(() => { blinkL = blinkR = 0; }, 120);
  }
}, 100);

// 启动
init();
</script>
</body>
</html>
''';
  }

  // ===== 公开接口 =====
  Future<void> setSpeaking(double intensity) async {
    if (!_loaded || _ctrl == null) return;
    await _ctrl!.runJavaScript('targetMouth = ${intensity.clamp(0, 1)};');
  }

  Future<void> setSilent() async {
    if (!_loaded || _ctrl == null) return;
    await _ctrl!.runJavaScript('targetMouth = 0;');
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return SizedBox(
        height: widget.height,
        child: Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.error_outline, size: 24, color: Colors.white.withOpacity(0.15)),
            const SizedBox(height: 4),
            Text('Live2D: $_error', style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.2))),
          ]),
        ),
      );
    }
    return SizedBox(
      height: widget.height,
      child: _ctrl == null
          ? const Center(child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF00D4AA)))
          : WebViewWidget(controller: _ctrl!),
    );
  }
}
