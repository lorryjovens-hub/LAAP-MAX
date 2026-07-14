import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:camera/camera.dart';
import 'package:path_provider/path_provider.dart';

class VisionScreen extends ConsumerStatefulWidget {
  const VisionScreen({super.key});
  @override
  ConsumerState<VisionScreen> createState() => _VisionScreenState();
}

class _VisionScreenState extends ConsumerState<VisionScreen> with WidgetsBindingObserver {
  CameraController? _cam;
  List<CameraDescription>? _cams;
  bool _init = false;
  bool _front = false;

  @override
  void initState() { super.initState(); WidgetsBinding.instance.addObserver(this); _initCam(); }
  @override
  void dispose() { WidgetsBinding.instance.removeObserver(this); _cam?.dispose(); super.dispose(); }
  @override
  void didChangeAppLifecycleState(AppLifecycleState s) {
    if (s == AppLifecycleState.paused) { _cam?.dispose(); _init = false; }
    else if (s == AppLifecycleState.resumed) _initCam();
  }

  Future<void> _initCam() async {
    try {
      _cams = await availableCameras();
      if (_cams == null || _cams!.isEmpty) return;
      final idx = _front ? 1 : 0;
      if (idx >= _cams!.length) return;
      _cam = CameraController(_cams![idx], ResolutionPreset.medium);
      await _cam!.initialize();
      if (mounted) setState(() => _init = true);
    } catch (_) {}
  }

  Future<void> _switch() async {
    if (_cams == null || _cams!.length < 2) return;
    await _cam?.dispose();
    _front = !_front;
    _init = false;
    await _initCam();
  }

  Future<void> _photo() async {
    if (!_init || _cam == null) return;
    try {
      final photo = await _cam!.takePicture();
      final dir = await getApplicationDocumentsDirectory();
      await photo.saveTo('${dir.path}/aris_${DateTime.now().millisecondsSinceEpoch}.jpg');
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('照片已保存'), duration: Duration(seconds: 2)));
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Expanded(
        child: _init && _cam != null
            ? ClipRRect(borderRadius: BorderRadius.circular(0), child: CameraPreview(_cam!))
            : GestureDetector(
                onTap: _initCam,
                child: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.camera_alt_outlined, size: 40, color: Colors.white.withOpacity(0.15)),
                  const SizedBox(height: 8),
                  Text('轻触启动摄像头', style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.25))),
                ])),
              ),
      ),
      Container(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          GestureDetector(onTap: _switch, child: Container(width:40,height:40,decoration:BoxDecoration(shape:BoxShape.circle,color:Colors.white.withOpacity(0.1)),
            child: Icon(Icons.flip_camera_ios, size:20, color:Colors.white.withOpacity(0.6)))),
          const SizedBox(width:40),
          GestureDetector(onTap: _photo, child: Container(width:60,height:60,decoration:BoxDecoration(shape:BoxShape.circle,border:Border.all(color:Colors.white.withOpacity(0.2),width:2)),
            child: Container(margin:const EdgeInsets.all(5),decoration:BoxDecoration(shape:BoxShape.circle,color:Colors.white.withOpacity(0.1))))),
          const SizedBox(width:40),
          Container(width:40,height:40,decoration:BoxDecoration(shape:BoxShape.circle,color:Colors.white.withOpacity(0.06))),
        ]),
      ),
    ]);
  }
}
