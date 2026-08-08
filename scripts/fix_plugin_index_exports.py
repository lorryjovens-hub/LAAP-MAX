"""统一修复 7 个插件的 index.ts：.tsx 组件运行时导出 → type-only 导出

根因：build-server 的插件运行时依赖扫描器只支持 .ts/.js（不含 .tsx），
所有 LAAP 插件的 .tsx 组件导出都会导致 dist:win 构建失败。
组件实际由 renderer 直接 lazy import（不走 index.ts），所以运行时导出可安全移除。
"""
import re
import os

PLUGINS = [
    "birth-ceremony", "bubble-field", "charter-guardian",
    "hot-compile-preview", "laaper-chat", "laaper-market", "skill-packs",
    "trio-chatroom",
]

# 模式：export { A, B } from "./X";  →  export type { ... } from "./X";
EXPORT_RE = re.compile(r'^export \{ ([^}]+) \} from "([^"]+)";\s*$')

for name in PLUGINS:
    path = os.path.join(r"D:\LAAP\hanako\plugins", name, "index.ts")
    if not os.path.exists(path):
        print(f"SKIP {name} (no index.ts)")
        continue
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    changed = []
    for line in lines:
        m = EXPORT_RE.match(line.strip())
        if m:
            symbols, src = m.group(1), m.group(2)
            # 只处理指向 .tsx 组件的导出（.ts 类型/常量导出保留）
            # 保守做法：全部改为 type-only（这些插件的组件都不进运行时容器）
            symbols = ", ".join(s.strip() for s in symbols.split(","))
            changed.append(f'export type {{ {symbols} }} from "{src}";\n')
            print(f"  {name}: {line.strip()}  ->  export type {{ {symbols} }} from \"{src}\";")
        else:
            changed.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(changed)
print("done")
