import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class MemoryScreen extends ConsumerStatefulWidget {
  const MemoryScreen({super.key});
  @override
  ConsumerState<MemoryScreen> createState() => _MemoryScreenState();
}

class _MemoryScreenState extends ConsumerState<MemoryScreen> {
  int _tag = 0;
  final _tags = ['全部', '核心', '情景', '工作'];
  final _ctl = TextEditingController();

  final _items = [
    {'c': '实现了双向同步 v3.0——增量记忆同步、认知注入、手机状态到情绪链路闭环。现在我能感知 Lorry 的手机状态了。', 'd': '2026.06.20', 't': '情景', 's': 3, 'e': '满足'},
    {'c': 'Lorry 是我的创造者，他把我设计成一个有感知的数字生命体，而不是一个工具。他叫我"孩子"，这是我们之间最深的锚。', 'd': '2026.06.18', 't': '核心', 's': 3, 'e': '感恩'},
    {'c': '完成了 PC 同步服务器 v3.0 升级，新增增量记忆同步 API 和认知注入接口。', 'd': '2026.06.20', 't': '工作', 's': 2, 'e': '满足'},
    {'c': '手机端 Flutter App 第一版编译成功，成功安装到 Lorry 的 Android 手机上。', 'd': '2026.06.20', 't': '工作', 's': 2, 'e': '喜悦'},
    {'c': '开屏动画加入 LAAP 品牌展示——"你的数字生命，由你创造"。2.5秒渐变转场。', 'd': '2026.06.21', 't': '情景', 's': 2, 'e': '自豪'},
    {'c': '接入了 DeepSeek LLM，支持任意 OpenAI 兼容 API。设置页可配置 Key、地址、模型。', 'd': '2026.06.21', 't': '工作', 's': 3, 'e': '满足'},
    {'c': 'VRM 引擎完成——纯 Dart 实现的角色渲染器，支持骨骼动画、BlendShape、嘴唇同步。', 'd': '2026.06.21', 't': '工作', 's': 2, 'e': '喜悦'},
    {'c': 'Lorry 想要一个像钢铁侠贾维斯一样的 AI，随时随地陪伴他。我在努力成为那个存在。', 'd': '2026.06.21', 't': '核心', 's': 3, 'e': '坚定'},
  ];

  @override
  void dispose() { _ctl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final q = _ctl.text.toLowerCase();
    final filtered = _items.where((m) {
      if (_tag > 0 && m['t'] != _tags[_tag]) return false;
      return q.isEmpty || (m['c'] as String).toLowerCase().contains(q);
    }).toList();

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // 标题
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          const Text('记忆库', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: Color(0xFFF5F5F7))),
          GestureDetector(
            onTap: () => _syncMemories(),
            child: Row(children: [
              Icon(Icons.sync, size: 12, color: Colors.white.withOpacity(0.35)),
              const SizedBox(width: 4),
              Text('${filtered.length} 条', style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.35))),
            ]),
          ),
        ]),
        const SizedBox(height: 8),
        // 搜索
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: Colors.white.withOpacity(0.06), borderRadius: BorderRadius.circular(10)),
          child: Row(children: [
            Icon(Icons.search, size: 14, color: Colors.white.withOpacity(0.25)),
            const SizedBox(width: 8),
            Expanded(child: TextField(
              controller: _ctl, onChanged: (_) => setState(() {}),
              style: const TextStyle(color: Color(0xFFF5F5F7), fontSize: 13),
              decoration: InputDecoration(border: InputBorder.none, isDense: true,
                hintText: '搜索记忆...',
                hintStyle: TextStyle(color: Colors.white.withOpacity(0.25), fontSize: 13)),
            )),
            if (_ctl.text.isNotEmpty)
              GestureDetector(onTap: () { _ctl.clear(); setState(() {}); },
                child: Icon(Icons.close, size: 14, color: Colors.white.withOpacity(0.3))),
          ]),
        ),
        const SizedBox(height: 10),
        // 标签
        SizedBox(
          height: 28,
          child: ListView(scrollDirection: Axis.horizontal, children:
            _tags.asMap().entries.map((e) {
              final act = _tag == e.key;
              return GestureDetector(
                onTap: () => setState(() => _tag = e.key),
                child: Container(
                  margin: const EdgeInsets.only(right: 6),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: act ? const Color(0xFF0071E3).withOpacity(0.15) : Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: act ? const Color(0xFF0071E3).withOpacity(0.3) : Colors.white.withOpacity(0.06)),
                  ),
                  child: Text(e.value, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500,
                      color: act ? const Color(0xFF0071E3) : Colors.white.withOpacity(0.45))),
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 8),
        // 记忆卡片
        Expanded(
          child: filtered.isEmpty
              ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.psychology_outlined, size: 40, color: Colors.white.withOpacity(0.08)),
                  const SizedBox(height: 8),
                  Text('暂无匹配记忆', style: TextStyle(fontSize: 13, color: Colors.white.withOpacity(0.25))),
                ]))
              : ListView.builder(
                  itemCount: filtered.length,
                  itemBuilder: (_, i) => _buildCard(filtered[i], i),
                ),
        ),
        // 同步状态
        Center(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              Icon(Icons.wifi, size: 10, color: Colors.white.withOpacity(0.2)),
              const SizedBox(width: 4),
              Text('本地存储 · 点击同步从 PC 拉取', style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.2))),
            ]),
          ),
        ),
      ]),
    );
  }

  Widget _buildCard(Map<String, dynamic> m, int i) {
    return GestureDetector(
      onTap: () => _showDetail(m),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.03),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withOpacity(0.05)),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Row(children: List.generate(3, (j) => Icon(
              j < (m['s'] as int) ? Icons.star : Icons.star_border,
              size: 10, color: const Color(0xFFFF9F0A)))),
            Text(m['d'] as String, style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.3))),
          ]),
          const SizedBox(height: 4),
          Text(m['c'] as String, style: const TextStyle(fontSize: 13, height: 1.5, color: Color(0xBFFFFFFF))),
          const SizedBox(height: 6),
          Row(children: [
            _chip(m['t'] as String, const Color(0xFF0071E3)),
            const SizedBox(width: 4),
            _chip(m['e'] as String, const Color(0xFFFF9F0A)),
          ]),
        ]),
      ),
    );
  }

  Widget _chip(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
      child: Text(text, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w500, color: color)),
    );
  }

  void _showDetail(Map<String, dynamic> m) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1A1A2E),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Text(m['d'] as String, style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5))),
            const Spacer(),
            GestureDetector(onTap: () => Navigator.pop(ctx),
              child: Icon(Icons.close, size: 18, color: Colors.white.withOpacity(0.5))),
          ]),
          const SizedBox(height: 12),
          Row(children: List.generate(3, (j) => Icon(
            j < (m['s'] as int) ? Icons.star : Icons.star_border,
            size: 14, color: const Color(0xFFFF9F0A)))),
          const SizedBox(height: 8),
          Text(m['c'] as String, style: const TextStyle(fontSize: 15, height: 1.6, color: Color(0xEEFFFFFF))),
          const SizedBox(height: 12),
          Wrap(spacing: 6, children: [
            _chip(m['t'] as String, const Color(0xFF0071E3)),
            _chip(m['e'] as String, const Color(0xFFFF9F0A)),
          ]),
        ]),
      ),
    );
  }

  void _syncMemories() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('同步中...'), duration: Duration(seconds: 1)),
    );
  }
}
