"""
LAAP UE5 场景操控 — 等 UE5 就绪后摆资产
"""
import requests, json, time, sys

RC = "http://127.0.0.1:30010"

def wait_ue5(timeout=90):
    for i in range(timeout):
        try:
            r = requests.get(f"{RC}/remote/info", timeout=2)
            if r.status_code == 200: return True
        except: pass
        if i % 10 == 0: print(f"等待 UE5... {i}s")
        time.sleep(1)
    return False

def py(code):
    r = requests.put(f"{RC}/remote/object/call", json={
        "objectPath": "/Script/Engine.Default__KismetSystemLibrary",
        "functionName": "ExecuteConsoleCommand",
        "parameters": {"Command": f"py {code}"}
    }, timeout=30)
    return r.json()

if not wait_ue5():
    print("UE5 未就绪")
    sys.exit(1)

print("\n✅ UE5 就绪！\n")

# 1. 查场景
print("📋 场景信息...")
r = py("""
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
print(f"Actor数: {len(actors)}")
""")
print(f"  {r}")

# 2. 搜资产
print("\n🔍 搜索可用的 StaticMesh...")
r = py("""
import unreal
reg = unreal.AssetRegistryHelpers.get_asset_registry()
meshes = reg.get_assets_by_class(unreal.StaticMesh.static_class())
print(f"StaticMesh数: {len(meshes)}")
for m in meshes[:8]:
    print(f"  {m.package_name}")
""")
print(f"  {r}")

# 3. 摆几个资产
print("\n🎯 正在摆资产到场景...")
r = py("""
import unreal
editor = unreal.EditorLevelLibrary
loc = unreal.Vector

# 放几个不同形状
items = [
    ("/Engine/BasicShapes/Cube", (300,0,100), "LAAP_Cube"),
    ("/Engine/BasicShapes/Sphere", (0,300,100), "LAAP_Sphere"),
    ("/Engine/BasicShapes/Cylinder", (-300,0,100), "LAAP_Cylinder"),
]

for path, pos, name in items:
    cls = unreal.load_asset(name_or_path=path).get_class()
    actor = editor.spawn_actor_from_class(cls, loc(*pos))
    if actor:
        actor.set_actor_label(name)
        print(f"  ✅ 已放置: {name}")

print("完成！")
""")
print(f"  {r}")

print("\n🎉 资产已摆好！看看 UE5 编辑器窗口。")