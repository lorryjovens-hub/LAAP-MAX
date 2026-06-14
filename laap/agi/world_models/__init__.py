"""
LAAP AGI — World Models Module
==============================

集成多种世界级开源世界模型：

1. LingBot-World (蚂蚁集团/Robbyant)
   - 实时3D环境生成
   - 16 FPS实时生成
   - 10+分钟时间一致性
   - 物理感知模拟

2. OpenWorldLib (北京大学/DataFlow)
   - 统一世界模型框架
   - 支持13+领先系统
   - 标准化接口和评估协议

3. HunYuanWorld (腾讯)
   - 实时交互式世界建模
   - 24 FPS流式视频生成
   - 长时几何一致性

使用方式：
    from laap.agi.world_models import LingBotWorldModel, OpenWorldLibModel, HunYuanWorldModel
    
    # 创建LingBot-World实例
    lingbot = LingBotWorldModel(api_key="your-api-key")
    
    # 创建OpenWorldLib实例
    openworld = OpenWorldLibModel(backend="hunyuan-worldplay")
    
    # 创建HunYuanWorld实例
    hunyuan = HunYuanWorldModel(api_key="your-api-key")
"""

from .lingbot import LingBotWorldModel
from .openworldlib import OpenWorldLibModel
from .hunyuan import HunYuanWorldModel

__all__ = [
    "LingBotWorldModel",
    "OpenWorldLibModel", 
    "HunYuanWorldModel"
]

__version__ = "1.0.0"
__description__ = "LAAP AGI World Models Integration Module"
__authors__ = ["LAAP Team"]