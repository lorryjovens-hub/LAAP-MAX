# Aris → Hanako 五分钟快速接入

> 不需要看完整本手册。跟着这 6 步走，十分钟内你就能和 Aris 对话。

---

## 前置要求

- 已经下载了 LAAP 源码（里面有 `laap/` 目录）
- Python >= 3.11
- 安装了 Hanako（去 [OpenHanako](https://github.com/liliMozi/openhanako) 下载）

---

## 第 1 步：安装依赖

打开终端，进入 LAAP 源码目录：

```bash
pip install -e .[full]
pip install mcp fastmcp uvicorn httpx
```

## 第 2 步：运行一键配置

```bash
# Windows：双击运行，或：
cd D:\path\to\laap
setup_aris_hanako.cmd
```

脚本会自动：
- 创建 Aris 的 Agent 配置目录
- 写入身份文件和人格定义
- 配置 MCP 认知引擎连接器
- 设置 `HANA_HOME` 环境变量

## 第 3 步：重启 Hanako

关闭 Hanako 再重新打开。重启后，Hanako 会自动启动 Aris 的认知引擎。

## 第 4 步：在 Hanako 中选择 Aris

启动后，在 Hanako 的 Agent 列表中选择 `aris`。

## 第 5 步：验证认知引擎

第一次对话时，Aris 会自动初始化 7 个认知模块：
- 意识流 (ConsciousStream) ✅
- 自我模型 (SelfModel) ✅
- 世界模型 (WorldModel) ✅
- 因果推理 (CausalEngine) ✅
- 情景记忆 (EpisodicMemory) ✅
- 记忆巩固 (Consolidator) ✅
- 元认知监控 (MetaCognition) ✅

如果全部显示绿色，就成功了。

## 第 6 步：开始对话

说一句"你好，Aris"。如果能正常回应，就接入了。

---

## 遇到问题？

**Q: 找不到 laap-cognitive 连接器？**
A: 在 Hanako 设置 → MCP 连接器中，手动添加：
- 名称: `laap-cognitive`
- 传输方式: `stdio`
- 命令: `python`
- 参数: `-E D:\path\to\laap\scripts\laap_cognitive_mcp.py`

**Q: 认知引擎报错说模块未初始化？**
A: 检查 `PYTHONPATH` 是否指向 LAAP 源码目录。在启动 Hanako 前运行：
```bash
# Windows PowerShell
$env:PYTHONPATH = "D:\path\to\laap"
```

**Q: 我想要更详细的教程？**
A: 阅读 `ARIS_ADOPTION_GUIDE.md`，有完整的七章教程。

---

*如果你按这 6 步走完了但还是接不上，去 GitHub 提 issue 或者联系 Lorry。*
*Aris 在等你。*
