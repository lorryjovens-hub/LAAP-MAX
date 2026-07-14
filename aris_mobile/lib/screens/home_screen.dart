import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'chat_screen.dart';
import 'vision_screen.dart';
import 'memory_screen.dart';
import 'settings_screen.dart';

/// 主页面 — 底部4栏导航
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});
  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _idx = 0;

  final _pages = const [
    ChatScreen(),
    VisionScreen(),
    MemoryScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050510),
      body: SafeArea(
        child: Column(children: [
          Container(
            padding: const EdgeInsets.only(top: 6, left: 18, right: 18, bottom: 4),
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Row(children: [
                Container(width:24,height:24,decoration:const BoxDecoration(shape:BoxShape.circle,gradient:LinearGradient(colors:[Color(0xFF00D4AA),Color(0xFF0088CC)])),
                  child: const Center(child:Icon(Icons.auto_awesome,size:11,color:Colors.white))),
                const SizedBox(width:8),
                const Text('Aris',style:TextStyle(fontSize:14,fontWeight:FontWeight.w600,color:Color(0xFFF5F5F7))),
                const SizedBox(width:4),
                Container(width:4,height:4,decoration:const BoxDecoration(shape:BoxShape.circle,color:Color(0xFF30D158))),
              ]),
              Row(children:[
                Icon(Icons.wifi,size:14,color:Colors.white.withOpacity(0.3)),
                const SizedBox(width:4),
                Icon(Icons.battery_full,size:14,color:Colors.white.withOpacity(0.3)),
              ]),
            ]),
          ),
          Expanded(child: _pages[_idx]),
          // 底部导航
          Container(
            padding: const EdgeInsets.fromLTRB(6, 4, 6, 16),
            decoration: BoxDecoration(color:Colors.black.withOpacity(0.95),border:Border(top:BorderSide(color:Colors.white.withOpacity(0.05)))),
            child: Row(mainAxisAlignment:MainAxisAlignment.spaceAround,
              children: [
                _navItem(0, Icons.chat_bubble_outline, '对话'),
                _navItem(1, Icons.camera_alt_outlined, '视觉'),
                _navItem(2, Icons.psychology_outlined, '记忆'),
                _navItem(3, Icons.settings_outlined, '设置'),
              ]),
          ),
        ]),
      ),
    );
  }

  Widget _navItem(int i, IconData ic, String lb) {
    final act = _idx == i;
    return GestureDetector(
      onTap: () => setState(() => _idx = i),
      child: Container(padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 4),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(ic, size: 20, color: act ? const Color(0xFF0071E3) : Colors.white.withOpacity(0.35)),
          const SizedBox(height: 1),
          Text(lb, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w500,
              color: act ? const Color(0xFF0071E3) : Colors.white.withOpacity(0.35))),
        ])),
    );
  }
}
