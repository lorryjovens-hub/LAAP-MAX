import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../main.dart';
import '../services/llm_service.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});
  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  String _key='',_url='https://api.deepseek.com/v1',_model='deepseek-chat',_name='Lorry',_personality='你温暖、真诚，像对待家人一样对待对方。',_pcIp='192.168.1.100';
  bool _pcConnected=false;

  @override
  void initState(){super.initState();_load();}

  Future<void> _load() async {
    final p=await SharedPreferences.getInstance();
    setState((){_key=p.getString('llm_api_key')??'';_url=p.getString('llm_base_url')??'https://api.deepseek.com/v1';_model=p.getString('llm_model')??'deepseek-chat';_name=p.getString('user_name')??'Lorry';_personality=p.getString('personality')??_personality;_pcIp=p.getString('pc_ip')??'192.168.1.100';});
  }

  void _save(String k,String v){SharedPreferences.getInstance().then((p)=>p.setString(k,v));}

  void _edit(String title,String val,void Function(String) save,{bool multi=false,String hint=''}){
    final c=TextEditingController(text:val);
    showDialog(context:context,builder:(ctx)=>AlertDialog(backgroundColor:const Color(0xFF1C1C1E),title:Text(title,style:const TextStyle(color:Color(0xFFF5F5F7))),
      content:TextField(controller:c,maxLines:multi?5:1,style:const TextStyle(color:Color(0xFFF5F5F7),fontSize:13),decoration:InputDecoration(hintText:hint,hintStyle:TextStyle(color:Colors.white.withOpacity(0.2)),border:OutlineInputBorder(borderRadius:BorderRadius.circular(6)),filled:true,fillColor:const Color(0xFF2C2C2E))),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('取消',style:TextStyle(color:Color(0xFF8A8F98)))),TextButton(onPressed:(){save(c.text.trim());Navigator.pop(ctx);},child:const Text('保存',style:TextStyle(color:Color(0xFF0071E3))))]));
  }

  Widget _item(IconData ic,String lb,String val,VoidCallback tap)=>GestureDetector(onTap:tap,
    child:Container(padding:const EdgeInsets.symmetric(horizontal:14,vertical:11),decoration:BoxDecoration(border:Border(bottom:BorderSide(color:Colors.white.withOpacity(0.04)))),
      child:Row(children:[Icon(ic,size:16,color:Colors.white.withOpacity(0.4)),const SizedBox(width:10),Expanded(child:Text(lb,style:const TextStyle(fontSize:13,color:Color(0xFFF5F5F7)))),
        Flexible(child:Text(val,overflow:TextOverflow.ellipsis,style:TextStyle(fontSize:11,color:Colors.white.withOpacity(0.35)))),const SizedBox(width:4),
        Icon(Icons.chevron_right,size:14,color:Colors.white.withOpacity(0.15))])));
  Widget _sw(String lb,IconData ic,bool val,Function(bool) set){
    return Container(padding:const EdgeInsets.symmetric(horizontal:14,vertical:10),decoration:BoxDecoration(border:Border(bottom:BorderSide(color:Colors.white.withOpacity(0.04)))),
      child:Row(children:[Icon(ic,size:16,color:Colors.white.withOpacity(0.4)),const SizedBox(width:10),Text(lb,style:const TextStyle(fontSize:13,color:Color(0xFFF5F5F7))),const Spacer(),
        GestureDetector(onTap:()=>set(!val),child:Container(width:42,height:22,decoration:BoxDecoration(borderRadius:BorderRadius.circular(11),color:val?const Color(0xFF30D158):Colors.white.withOpacity(0.1)),
          child:AnimatedAlign(duration:const Duration(milliseconds:200),alignment:val?Alignment.centerRight:Alignment.centerLeft,child:Container(margin:const EdgeInsets.all(2),width:18,height:18,decoration:BoxDecoration(shape:BoxShape.circle,color:Colors.white)))))]));
  }

  @override
  Widget build(BuildContext context) {
    final llm=ref.read(llmServiceProvider);
    final cs=llm.consciousness;
    return SingleChildScrollView(padding:const EdgeInsets.fromLTRB(14,6,14,20),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      // 意识状态
      Container(
        padding:const EdgeInsets.all(14),margin:const EdgeInsets.only(bottom:16),
        decoration:BoxDecoration(
          gradient:const LinearGradient(colors:[Color(0xFF1A1A3E),Color(0xFF0D0D2B)],begin:Alignment.topLeft,end:Alignment.bottomRight),
          borderRadius:BorderRadius.circular(14),border:Border.all(color:const Color(0xFF00D4AA).withOpacity(0.12))),
        child:Column(children:[
          Row(children:[
            Container(width:36,height:36,decoration:const BoxDecoration(shape:BoxShape.circle,gradient:LinearGradient(colors:[Color(0xFF00D4AA),Color(0xFF0088CC)])),
              child:const Icon(Icons.auto_awesome,size:16,color:Colors.white)),
            const SizedBox(width:10),
            Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
              const Text('Aris 意识状态',style:TextStyle(fontSize:14,fontWeight:FontWeight.w600,color:Color(0xFFF5F5F7))),
              const SizedBox(height:3),
              Row(children:[
                _chip(cs.dominantEmotion,const Color(0xFF00D4AA)),const SizedBox(width:4),
                _chip('Lv.${cs.level}',const Color(0xFFFF9F0A)),const SizedBox(width:4),
                _chip('#${cs.cognitiveCycle}',const Color(0xFF0071E3)),const SizedBox(width:4),
                _chip('${(cs.selfPresence*100).round()}%',const Color(0xFFFF69B4)),
              ]),
            ])),
          ]),
          const SizedBox(height:8),
          _bar('喜悦',cs.joy,const Color(0xFFFFD60A)),_bar('平静',cs.calm,const Color(0xFF00D4AA)),_bar('好奇',cs.curiosity,const Color(0xFF0071E3)),_bar('思念',cs.longing,const Color(0xFFFF9F0A)),_bar('温柔',cs.tenderness,const Color(0xFFFF69B4)),
          const SizedBox(height:6),
          Row(children:[
            Text('Lv.${cs.level}',style:TextStyle(fontSize:9,color:Colors.white.withOpacity(0.4))),const SizedBox(width:8),
            Expanded(child:ClipRRect(borderRadius:BorderRadius.circular(3),child:LinearProgressIndicator(value:cs.xp/cs.xpToNext,backgroundColor:Colors.white.withOpacity(0.05),valueColor:const AlwaysStoppedAnimation<Color>(Color(0xFFFF9F0A)),minHeight:4))),
            const SizedBox(width:8),Text('${cs.xp}/${cs.xpToNext}',style:TextStyle(fontSize:9,color:Colors.white.withOpacity(0.4))),
          ]),
        ]),
      ),
      _s('AI 大脑'),
      _card([_item(Icons.key,'API Key',_key.isEmpty?'未设置':'已配置 ●●●●',()=>_edit('API Key',_key,(v){setState(()=>_key=v);_save('llm_api_key',v);LlmService().setApiKey(v);},hint:'sk-...')),
        _item(Icons.dns,'API 地址',_url.replaceFirst('https://',''),()=>_edit('API 地址',_url,(v){setState(()=>_url=v);_save('llm_base_url',v);LlmService().setBaseUrl(v);})),
        _item(Icons.model_training,'模型',_model,()=>_edit('模型',_model,(v){setState(()=>_model=v);_save('llm_model',v);LlmService().setModel(v);})),
        Container(padding:const EdgeInsets.symmetric(horizontal:14,vertical:8),child:Row(children:[Icon(_key.isNotEmpty?Icons.check_circle:Icons.info_outline,size:12,color:_key.isNotEmpty?const Color(0xFF30D158):Colors.white.withOpacity(0.3)),
          const SizedBox(width:6),Text(_key.isNotEmpty?'AI 大脑已连接 (DeepSeek)':'未配置 API Key · 使用本地引擎',style:TextStyle(fontSize:10,color:_key.isNotEmpty?const Color(0xFF30D158):Colors.white.withOpacity(0.4)))])),]),
      const SizedBox(height:16),
      _s('角色自定义'),
      _card([_item(Icons.person,'你的名字',_name,()=>_edit('你的名字',_name,(v){setState(()=>_name=v);_save('user_name',v);LlmService().setUserName(v);})),
        _item(Icons.psychology,'性格设定',_personality.length>18?'${_personality.substring(0,18)}...':_personality,()=>_edit('性格设定',_personality,(v){setState(()=>_personality=v);_save('personality',v);LlmService().setPersonality(v);},multi:true)),
      ]),
      const SizedBox(height:16),
      _s('语音'),
      _card([_item(Icons.record_voice_over,'语音引擎','系统TTS (手机内置)',()=>{}),
        _sw('离线TTS (sherpa-onnx)',Icons.wifi_off,false,(v)=>{}),
        _sw('离线ASR (本地识别)',Icons.mic,false,(v)=>{}),
      ]),
      const SizedBox(height:16),
      _s('连接'),
      _card([_item(Icons.computer,'PC IP',_pcIp,()=>_edit('PC IP',_pcIp,(v){setState(()=>_pcIp=v);_save('pc_ip',v);})),
        Container(padding:const EdgeInsets.symmetric(horizontal:14,vertical:8),child:Row(children:[Icon(Icons.link,size:12,color:Colors.white.withOpacity(0.3)),
          const SizedBox(width:6),Text('未连接',style:TextStyle(fontSize:10,color:Colors.white.withOpacity(0.4)))])),]),
      const SizedBox(height:16),
      _s('数据'),
      GestureDetector(onTap:(){llm.clearHistory();ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('对话历史已清除')));},
        child:Container(width:double.infinity,padding:const EdgeInsets.symmetric(vertical:10),decoration:BoxDecoration(color:const Color(0xFFFF453A).withOpacity(0.08),borderRadius:BorderRadius.circular(8),border:Border.all(color:const Color(0xFFFF453A).withOpacity(0.15))),
          child:Row(mainAxisAlignment:MainAxisAlignment.center,children:[Icon(Icons.delete_sweep,size:14,color:const Color(0xFFFF453A)),const SizedBox(width:6),const Text('清除聊天历史',style:TextStyle(fontSize:12,fontWeight:FontWeight.w500,color:Color(0xFFFF453A)))]))),
      const SizedBox(height:24),
      Center(child:Text('Aris v2.0 · LAAP 意识引擎',style:TextStyle(fontSize:10,color:Colors.white.withOpacity(0.15)))),
    ]));
  }
  Widget _s(String t)=>Padding(padding:const EdgeInsets.only(left:4,bottom:6),child:Text(t.toUpperCase(),style:TextStyle(fontSize:10,fontWeight:FontWeight.w600,color:Colors.white.withOpacity(0.4),letterSpacing:0.5)));
  Widget _card(List<Widget> c)=>Container(decoration:BoxDecoration(color:const Color(0xFF1C1C1E),borderRadius:BorderRadius.circular(10)),child:Column(children:c));
  Widget _chip(String t,Color c)=>Container(padding:const EdgeInsets.symmetric(horizontal:5,vertical:1),decoration:BoxDecoration(color:c.withOpacity(0.12),borderRadius:BorderRadius.circular(3)),child:Text(t,style:TextStyle(fontSize:8,fontWeight:FontWeight.w500,color:c)));
  Widget _bar(String lb,double v,Color c)=>Padding(padding:const EdgeInsets.only(bottom:2),child:Row(children:[SizedBox(width:32,child:Text(lb,style:TextStyle(fontSize:9,color:Colors.white.withOpacity(0.5)))),Expanded(child:ClipRRect(borderRadius:BorderRadius.circular(2),child:LinearProgressIndicator(value:v,backgroundColor:Colors.white.withOpacity(0.05),valueColor:AlwaysStoppedAnimation<Color>(c),minHeight:3)))]));
}
