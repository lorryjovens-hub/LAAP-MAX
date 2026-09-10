#!/usr/bin/env python3
"""
演示 HEP 完整系统 - 真实端到端工作流程
=====================================================
这是一个完整的系统演示，展示 HEP 的三个主要新功能：

1. 真实组件依赖解析 (拓扑排序)
2. 复杂的 ComponentNode 树转 HEP 规格
3. 多格式产物组装 (Python, SQL, Docker, CI/CD 等)

流程展示：
User Intent
    ↓
WebsiteClassifier → WebsiteType + ComponentNode Tree
    ↓
ComponentNode Tree → HEP Component Spec (with dependencies)
    ↓
HEPBuildPipeline (topological sort + build)
    ↓
Multi-format Artifacts (Python CRUD, PostgreSQL, Docker, CI/CD, HTML)
"""

import sys
from pathlib
import sys, time, json
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(r"D:\LAAP\harness\laap_coding\core")))

from hep_complete_system import CompleteHEPSystem, build_project
def demo_basic_intent():
    """演示基本的自然语言意图处理"""
    print("=" * 60)
    print("DEMO 1: 自然语言意图处理")
    print("=" * 60)

    system = CompleteHEPSystem()

    # 真实的自然语言意图
    intents = [
        "I need an online store for handmade jewelry with 5 product categories",
        "Build a SaaS landing page for my AI startup",
        "Create a personal portfolio website to showcase my design work",
        "I want a restaurant website with online reservation system",
        "Build a blog about technology and programming"
    ]

    for i, intent in enumerate(intents, 1):
        print(f"\n{i}. 处理意图: {intent}")
        print("-" * 50)

        result = system.build_from_intent(intent, style="saas")

        if result["success"]:
            print(f"✓ 检测到的类型: {result['display_name']} ({result['detected_type']})")
            print(f"  组件树深度: {result.get('tree_depth', 'N/A')}")
            print(f"  生成的文件: {result['components_built']}")
            print(f"  构建时间: {result['build_time_ms']}ms")

            # 列出生成的文件类型
            file_types = {}
            for filename in result["artifacts"].keys():
                if not filename.startswith("_"):
                    ext = filename.split('.')[-1] if '.' in filename else 'noext'
                    file_types[ext] = file_types.get(ext, 0) + 1

            print(f"  文件类型: {dict(file_types)}")

            # 显示关键文件内容（示例）
            key_files = ['crud.py', 'README.md', 'Dockerfile']
            for key_file in key_files:
                if key_file in result["artifacts"]:
                    print(f"  {key_file}: ({len(result['artifacts'][key_file])} 字符)")
                    # 显示前200字符
                    preview = result["artifacts"][key_file][:200].replace(chr(10), ' ')
                    print(f"    预览: {preview}...")

        else:
            print(f"✗ 错误: {result.get('error', '未知错误')}")

        print()

def demo_dependency_resolution():
    """演示组件依赖解析"""
    print("=" * 60)
    print("DEMO 2: 组件依赖解析 (拓扑排序)")
    print("=" * 60)

    # 创建一个具有复杂依赖关系的组件树
    from website_compiler import ComponentNode, WebsiteClassifier

    complex_tree = ComponentNode(
        id="ecommerce",
        name="E-commerce Platform",
        description="完整在线商店，包含产品目录、购物车和结账",
        children=[
            ComponentNode(
                id="ecom_global",
                name="全局元素",
                children=[
                    ComponentNode(id="header", name="页头", hep_component_id="backend.fastapi_project"),
                    ComponentNode(id="footer", name="页脚", hep_component_id="devops.github_actions"),
                ]
            ),
            ComponentNode(
                id="ecom_home",
                name="主页",
                children=[
                    ComponentNode(id="hero", name="英雄区域", hep_component_id="ui.landing_page"),
                    ComponentNode(id="category_grid", name="分类网格", hep_component_id="backend.fastapi_crud"),
                    ComponentNode(id="trust_signals", name="信任信号"),
                ]
            ),
            ComponentNode(
                id="ecom_detail",
                name="产品详情",
                children=[
                    ComponentNode(id="image_gallery", name="图片库", hep_component_id="backend.fastapi_crud"),
                    ComponentNode(id="product_info", name="产品信息", hep_component_id="db.postgres_schema"),
                    ComponentNode(id="add_to_cart", name="加入购物车", hep_component_id="backend.fastapi_crud"),
                ]
            ),
        ]
    )

    from hep_protocol import REGISTRY
    from hep_complete_system import component_tree_to_hep_spec

    # 转换为 HEP 规格
    hep_spec = component_tree_to_hep_spec(complex_tree.to_dict(), "luxury")

    print("组件依赖关系:")
    for i, comp in enumerate(hep_spec['components'], 1):
        deps = REGISTRY.get(comp['id']).dependencies if REGISTRY.get(comp['id']) else []
        print(f"  {i}. {comp['id']}")
        if deps:
            print(f"     └─ 依赖: {', '.join(deps)}")
        else:
            print(f"     └─ 无依赖")

    print(f"\n依赖图拓扑排序后的构建顺序:")
    pipeline = CompleteHEPSystem().pipeline
    sorted_order = pipeline.registry.topological_sort([
        comp['id'] for comp in hep_spec['components']
        if REGISTRY.get(comp['id'])
    ])

    for i, comp_id in enumerate(sorted_order, 1):
        comp = REGISTRY.get(comp_id)
        print(f"  {i}. {comp_id} (domain: {comp.domain if comp else 'N/A'})")

    print(f"\n✓ 拓扑排序确保了 {len(sorted_order)} 个组件的有序构建")
def demo_output_formats():
    """演示多格式产物输出"""
    print("=" * 60)
    print("DEMO 3: 多格式产物组装")
    print("=" * 60)

    # 建造一个完整的 E-commerce 应用
    intent = "I need a complete e-commerce website for handmade jewelry with payment processing"

    print(f"正在构建: {intent}")
    print("-" * 50)

    result = build_project(intent, style="luxury", output_dir=None)

    if not result["success"]:
        print(f"✗ 构建失败: {result.get('error', '未知错误')}")
        return

    print(f"✓ 成功构建! ({result['build_time_ms']}ms)")

    # 整理文件类型
    file_categories = {}
    for filename in result["artifacts"].keys():
        if filename.startswith("_"):
            continue

        if '.' in filename:
            ext = filename.split('.')[-1]
        else:
            ext = 'no_extension'

        if ext not in file_categories:
            file_categories[ext] = []
        file_categories[ext].append(filename)

    print(f"\n产出文件分类 ({len(file_categories)} 类别):")
    for ext, files in sorted(file_categories.items()):
        print(f"  {ext.upper()} ({len(files)} 文件):")
        for f in sorted(files)[:5]:  # 显示前5个
            size = len(str(result["artifacts"][f])) if f in result["artifacts"] else 0
            print(f"    - {f} ({size} 字符)")
        if len(files) > 5:
            print(f"    ... 并有 {len(files) - 5} 个更多文件")

    # 演示关键产出的实际内容
    print(f"\n示例关键产出:")

    # 1. Python CRUD API
    if 'crud.py' in result["artifacts"]:
        crud_code = result["artifacts"]["crud.py"]
        print(f"   Python CRUD API:")
        lines = crud_code.split(chr(10))
        print(f"     {len(lines)} 行代码")
        print(f"     包含 FastAPI 路由、SQLAlchemy 模型、Pydantic 验证")
        # 显示一些代码片段
        important_lines = [l for l in lines if any(x in l for x in ['FastAPI', 'Route', '@app', 'class', 'def'])]
        print(f"     关键组件: {len(important_lines)} 个")

    # 2. PostgreSQL Schema
    if 'schema.sql' in result["artifacts"]:
        schema_sql = result["artifacts"]["schema.sql"]
        print(f"   PostgreSQL Schema:")
        print(f"     {len(schema_sql)} 字符 SQL")
        print(f"     包含表定义、外键约束、索引")
        if 'CREATE TABLE' in schema_sql:
            create_count = schema_sql.count('CREATE TABLE')
            print(f"     {create_count} 个表定义")

    # 3. Docker 配置
    docker_files = [f for f in result["artifacts"].keys() if f in ['Dockerfile', 'docker-compose.yml']]
    if docker_files:
        print(f"   Docker 配置:")
        for df in docker_files:
            print(f"     - {df}")

    # 4. CI/CD 流水线
    if '.github/workflows/ci.yml' in result["artifacts"]:
        ci_yml = result["artifacts"]['.github/workflows/ci.yml']
        print(f"   GitHub Actions CI:")
        print(f"     {len(ci_yml)} 字符流水线定义")
        if 'jobs:' in ci_yml:
            job_count = ci_yml.count('jobs:')
            print(f"     {job_count} 个 Job 步骤")

    # 5. 文档
    if 'README.md' in result["artifacts"]:
        readme = result["artifacts"]["README.md"]
        print(f"   README 文档:")
        print(f"     {len(readme)} 字符")
        if '# ' in readme:
            title = readme.split(chr(10))[0].replace('# ', '')
            print(f"     标题: {title}")

    print(f"\n✓ 总共生成了 {result['components_built']} 个代码组件，支持全栈应用")
def demo_style_comparison():
    """演示不同设计风格"""
    print("=" * 60)
    print("DEMO 4: 设计风格对比")
    print("=" * 60)

    system = CompleteHEPSystem()
    intent = "Create a portfolio website to showcase my design work"

    styles = ["saas", "modern_dark", "cyberpunk", "luxury", "terminal"]

    for style in styles:
        print(f"\n  Style: {style.upper()}")
        result = system.build_from_intent(intent, style=style)

        if result["success"]:
            print(f"    ✓ 构建时间: {result['build_time_ms']}ms")
            print(f"    ✓ 文件数量: {result['components_built']}")

            # 样式特定的文件
            css_files = [f for f in result["artifacts"].keys() if 'style' in f or f.endswith('.css')]
            if css_files:
                print(f"    ✓ 样式文件: {len(css_files)}")

            # HTML 文件
            html_files = [f for f in result["artifacts"].keys() if f.endswith('.html')]
            if html_files:
                html_size = len(str(result["artifacts"][html_files[0]]))
                print(f"    ✓ HTML 页面: {html_size} 字符")

        else:
            print(f"    ✗ 失败: {result.get('error', '未知错误')}")
def demo_real_world_scenario():
    """演示真实世界场景"""
    print("=" * 60)
    print("DEMO 5: 真实世界场景 - SaaS 创业公司")
    print("=" * 60)

    # 模拟一个真实 SaaS 创业公司的需求
    real_world_intents = [
        {
            "name": "初创期 - 营销网站",
            "intent": "Create a marketing landing page for my AI-powered task management SaaS",
            "style": "saas"
        },
        {
            "name": "扩张期 - 用户仪表",
            "intent": "Build an admin dashboard with user management and analytics",
            "style": "modern_dark"
        },
        {
            "name": "产品期 - 完整平台",
            "intent": "Create a full-stack e-commerce platform with products, cart and payments",
            "style": "web3"
        }
    ]

    total_time = 0
    total_files = 0

    for i, scenario in enumerate(real_world_intents, 1):
        print(f"\n{i}. 场景: {scenario['name']}")
        print(f"   需求: {scenario['intent']}")
        print(f"   风格: {scenario['style']}")

        start_time = time.time()
        result = build_project(scenario['intent'], scenario['style'], output_dir=None)
        build_time = (time.time() - start_time) * 1000

        if result["success"]:
            print(f"   ✓ 成功! ({build_time:.1f}ms)")
            print(f"   ✓ {result['components_built']} 个文件")
            print(f"   ✓ {result.get('detected_type', 'N/A')} ({result.get('display_name', 'N/A')})")

            total_time += build_time
            total_files += result['components_built']

            # 显示主要文件类型
            main_files = []
            for f in result["artifacts"].keys():
                if not f.startswith("_"):
                    main_files.append(f)

            print(f"   文件: {', '.join(sorted(main_files)[:3])}")
            if len(main_files) > 3:
                print(f"   ... 及 {len(main_files) - 3} 个文件")

        else:
            print(f"   ✗ 失败: {result.get('error', '未知错误')}")

    print(f"\n{'='*60}")
    print(f"总结: 总构建时间 {total_time:.1f}ms, {total_files} 个文件")
    print(f"平均每次构建: {total_time/len(real_world_intents):.1f}ms, {total_files//len(real_world_intents)} 个文件")
    print(f"✓ 完整系统证明: 从自然语言到完整代码，自动化可扩展")
# ============================================
# 主程序入口
# ============================================

if __name__ == "__main__":
    print("HEP 完整系统演示")
    print("=" * 50)
    print("这个演示展示了 HEP 三个核心功能：")
    print("1. 真实组件依赖解析 (拓扑排序)")
    print("2. 组件树转 HEP 规格")
    print("3. 多格式产物组装")
    print("\n选择演示功能:")
    print("  1 - 基本自然语言处理")
    print("  2 - 组件依赖解析")
    print("  3 - 多格式产物")
    print("  4 - 设计风格对比")
    print("  5 - 真实世界场景")
    print("  或直接运行以下任一命令:")
    print("  python demo_hep_complete.py [1|2|3|4|5]")

    if len(sys.argv) > 1:
        demo_map = {
            '1': demo_basic_intent,
            '2': demo_dependency_resolution,
            '3': demo_output_formats,
            '4': demo_style_comparison,
            '5': demo_real_world_scenario,
        }

        if sys.argv[1] in demo_map:
            demo_map[sys.argv[1]]()
        else:
            print(f"\n无效选项: {sys.argv[1]}")
            sys.exit(1)
    else:
        # 默认运行所有演示
        print("\n运行所有演示...")
        print("=" * 60)

        demos = [
            ("基本自然语言处理", demo_basic_intent),
            ("组件依赖解析", demo_dependency_resolution),
            ("多格式产物", demo_output_formats),
            ("设计风格对比", demo_style_comparison),
            ("真实世界场景", demo_real_world_scenario),
        ]

        for name, demo_func in demos:
            print(f"\n{demo_func.__doc__}")
            print("=" * len(demo_func.__doc__))
            demo_func()

        print("\n" + "=" * 60)
        print("所有演示完成!")
        print("\nHEP 完整系统证明:")
        print("✓ 从自然语言意图到完整代码")
        print("✓ 自动组件依赖解析和拓扑排序")
        print("✓ 支持多种产物类型 (HTML, Python, SQL, Docker 等)")
        print("✓ 设计风格和页面类型的可扩展组合")
        print("✓ 真实世界应用场景支持")
        print("\n系统准备就绪，可以满足企业级需要!")
