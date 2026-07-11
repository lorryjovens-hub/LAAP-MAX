"""精确替换 PhysicsVehicle.tsx 中的 scale.setScalar(1) 为 scale.setScalar(0.01)"""
from pathlib import Path

f = Path(r"D:\ai-website-cloner-template-master\src\components\three\PhysicsVehicle.tsx")
content = f.read_text(encoding="utf-8")

old = """    // 车辆模型缩放调整以匹配物理底盘尺寸
    // GLB 模型原始尺寸较大，需要缩放到物理尺寸
    carGltf.scene.scale.setScalar(1);"""

new = """    // 车辆模型缩放：GLB 原始尺寸约为物理底盘的 100 倍
    // 与 CarModel 静态预览一致使用 0.01，让视觉尺寸匹配 chassisSize (1.9x0.5x3.5)
    carGltf.scene.scale.setScalar(0.01);"""

if old in content:
    content = content.replace(old, new, 1)
    f.write_text(content, encoding="utf-8")
    print("OK: scale.setScalar(1) -> scale.setScalar(0.01)")
else:
    print("FAIL: old text not found")
    # 检查是否已经被替换
    if "scale.setScalar(0.01)" in content:
        print("ALREADY REPLACED")
