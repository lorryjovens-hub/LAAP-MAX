"""
hep_protocol.py — HEP 组件注册表（重建版 v2.0.0）
====================================================
HEP (Harness Engineering Protocol) — 零 Token 生成管线组件注册表。

2026-08-03 重建：原文件损坏（缺失类定义/注册表/生成器实现），
依据残留注册清单 + HEP_COMMERCIAL_PIPELINE.md 设计意图完整修复。

用法:
    from hep_protocol import REGISTRY, HEPComponent
    comps = REGISTRY.search(domain="codegen")
    out = comps[0].generate({"model_name": "User", "fields": [...]})
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
# 1. HEPComponent — 组件定义
# ═══════════════════════════════════════════════════════════════

class HEPComponent:
    """一个可注册、可检索、可执行的零 Token 生成组件。"""

    def __init__(
        self,
        id: str,
        name: str,
        version: str = "1.0.0",
        domain: str = "general",
        subdomain: str = "",
        tags: Optional[List[str]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, str]] = None,
        dependencies: Optional[List[str]] = None,
        generator: Optional[Callable[[Dict[str, Any]], Dict[str, str]]] = None,
    ):
        self.id = id
        self.name = name
        self.version = version
        self.domain = domain
        self.subdomain = subdomain
        self.tags = tags or []
        self.inputs = inputs or {}
        self.outputs = outputs or {}
        self.dependencies = dependencies or []
        self.generator = generator

    def generate(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """执行生成器。返回 {output_path: content}。"""
        if self.generator is None:
            raise NotImplementedError(f"HEP component '{self.id}' has no generator")
        return self.generator(inputs)

    def describe(self) -> str:
        return (
            f"[{self.id}] {self.name} v{self.version} "
            f"({self.domain}/{self.subdomain}) tags={','.join(self.tags)}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "tags": self.tags,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "has_generator": self.generator is not None,
        }


# ═══════════════════════════════════════════════════════════════
# 2. HEPRegistry — 注册表
# ═══════════════════════════════════════════════════════════════

class HEPRegistry:
    """HEP 组件注册表：register / search / list。"""

    def __init__(self):
        self.components: Dict[str, HEPComponent] = {}
        self._by_domain: Dict[str, List[str]] = {}

    def register(self, comp: HEPComponent) -> None:
        self.components[comp.id] = comp
        self._by_domain.setdefault(comp.domain, []).append(comp.id)

    def get(self, comp_id: str) -> Optional[HEPComponent]:
        return self.components.get(comp_id)

    def search(self, domain: Optional[str] = None, tag: Optional[str] = None) -> List[HEPComponent]:
        """按 domain / tag 检索组件列表。"""
        ids = self._by_domain.get(domain, list(self.components.keys())) if domain else list(self.components.keys())
        results = []
        for cid in ids:
            comp = self.components.get(cid)
            if comp is None:
                continue
            if tag and tag not in comp.tags:
                continue
            results.append(comp)
        return results

    def list(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self.components.values()]

    @property
    def count(self) -> int:
        return len(self.components)


REGISTRY = HEPRegistry()


# ═══════════════════════════════════════════════════════════════
# 3. 生成器实现（零 Token 模板生成）
# ═══════════════════════════════════════════════════════════════

def _table_defs(fields: Any) -> str:
    """把字段定义转成 SQLAlchemy 列定义。"""
    if isinstance(fields, list):
        return "\n".join(f"    {f} = Column(String)" if isinstance(f, str) else f"    {f}" for f in fields)
    return "    name = Column(String)"


def gen_fastapi_crud(inputs: Dict[str, Any]) -> Dict[str, str]:
    model = inputs.get("model_name", "Item")
    fields = inputs.get("fields", [])
    cols = _table_defs(fields)
    return {
        "output.py": f'''"""Auto-generated FastAPI CRUD for {model} (HEP 0-token)"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="{model} API")

class {model}Create(BaseModel):
{chr(10).join(f"    {f}: str = ..." if isinstance(f, str) else f"    {f}" for f in (fields or ["name"]))}

class {model}Out({model}Create):
    id: int

_db: List[dict] = []
_counter = 0

@app.post("/{model.lower()}/", response_model={model}Out)
def create(item: {model}Create):
    global _counter
    _counter += 1
    rec = {{"id": _counter, **item.model_dump()}}
    _db.append(rec)
    return rec

@app.get("/{model.lower()}/", response_model=List[{model}Out])
def list_items():
    return _db

@app.get("/{model.lower()}/{{item_id}}", response_model={model}Out)
def get_item(item_id: int):
    for rec in _db:
        if rec["id"] == item_id:
            return rec
    raise HTTPException(404, "not found")

@app.delete("/{model.lower()}/{{item_id}}")
def delete_item(item_id: int):
    global _db
    before = len(_db)
    _db = [r for r in _db if r["id"] != item_id]
    if len(_db) == before:
        raise HTTPException(404, "not found")
    return {{"deleted": item_id}}
''',
    }


def gen_fastapi_project(inputs: Dict[str, Any]) -> Dict[str, str]:
    name = inputs.get("project_name", "myapi")
    return {
        "main.py": f'''"""FastAPI project: {name} (HEP 0-token)"""
from fastapi import FastAPI

app = FastAPI(title="{name}")

@app.get("/")
def root():
    return {{"service": "{name}", "status": "ok"}}
''',
        "Dockerfile": f'''FROM python:3.12-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
        "README.md": f"# {name}\n\nAuto-generated by HEP 0-token pipeline.\n",
    }


def gen_django_project(inputs: Dict[str, Any]) -> Dict[str, str]:
    name = inputs.get("project_name", "myproject")
    apps = inputs.get("apps", [])
    app_lines = "\n".join(f"    '{a}'," for a in apps)
    return {
        "manage.py": f'''#!/usr/bin/env python
"""Django management script for {name}"""
import os, sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{name}.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
''',
        "settings.py": f'''"""Django settings for {name}"""
SECRET_KEY = "hep-0token-dev-key"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
{app_lines}
]
ROOT_URLCONF = "{name}.urls"
DATABASES = {{"default": {{"ENGINE": "django.db.backends.sqlite3", "NAME": "db.sqlite3"}}}}
''',
        "apps/__init__.py": "",
    }


def gen_postgres_schema(inputs: Dict[str, Any]) -> Dict[str, str]:
    tables = inputs.get("tables", [{"name": "users", "columns": [("id", "SERIAL PRIMARY KEY"), ("name", "TEXT")]}])
    lines = []
    for t in tables:
        tname = t.get("name", "table") if isinstance(t, dict) else t
        cols = t.get("columns", [("id", "SERIAL PRIMARY KEY")]) if isinstance(t, dict) else [("id", "SERIAL PRIMARY KEY")]
        col_sql = ",\n    ".join(f"{c[0]} {c[1]}" if isinstance(c, (list, tuple)) else f"{c}" for c in cols)
        lines.append(f"CREATE TABLE IF NOT EXISTS {tname} (\n    {col_sql}\n);")
    return {"schema.sql": "\n\n".join(lines) + "\n"}


def gen_dockerfile(inputs: Dict[str, Any]) -> Dict[str, str]:
    base = inputs.get("base_image", "python:3.12-slim")
    port = inputs.get("port", 8000)
    return {
        "Dockerfile": f'''FROM {base}
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["python", "main.py"]
''',
        ".dockerignore": "*.pyc\n.venv/\n__pycache__/\n.git/\n",
    }


def gen_docker_compose(inputs: Dict[str, Any]) -> Dict[str, str]:
    services = inputs.get("services", [{"name": "app", "image": "python:3.12-slim", "port": "8000:8000"}])
    lines = ["services:"]
    for s in services:
        sname = s.get("name", "app") if isinstance(s, dict) else s
        image = s.get("image", "python:3.12-slim") if isinstance(s, dict) else "python:3.12-slim"
        port = s.get("port", "8000:8000") if isinstance(s, dict) else "8000:8000"
        lines.append(f"  {sname}:")
        lines.append(f"    image: {image}")
        lines.append(f"    ports:")
        lines.append(f'      - "{port}"')
    return {"docker-compose.yml": "\n".join(lines) + "\n"}


def gen_github_actions(inputs: Dict[str, Any]) -> Dict[str, str]:
    framework = inputs.get("framework", "python")
    test_cmd = inputs.get("test_cmd", "pytest")
    return {
        ".github/workflows/ci.yml": f'''name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-{framework}@v5
        with:
          {framework}-version: "3.12"
      - run: pip install -r requirements.txt
      - run: {test_cmd}
''',
    }


def gen_readme(inputs: Dict[str, Any]) -> Dict[str, str]:
    name = inputs.get("project_name", "My Project")
    desc = inputs.get("description", "")
    return {
        "README.md": f"""# {name}

{desc}

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

_Generated by HEP 0-token pipeline._
""",
    }


# ═══════════════════════════════════════════════════════════════
# 4. 默认注册
# ═══════════════════════════════════════════════════════════════

def register_defaults() -> None:
    """注册全部 HEP 组件（幂等，可重复调用）。"""
    if REGISTRY.count > 0:
        return

    # --------------------------------------------------------------------
    # Python generators
    REGISTRY.register(HEPComponent(
        id="gen.fastapi.crud",
        name="FastAPI CRUD Generator",
        version="2.0.0",
        domain="codegen",
        subdomain="generator",
        tags=["python", "fastapi", "crud", "generator"],
        inputs={"model_name": {"type": "string"}, "fields": {"type": "array"}},
        outputs={"output.py": "python"},
        dependencies=[],
        generator=gen_fastapi_crud,
    ))

    REGISTRY.register(HEPComponent(
        id="gen.fastapi.project",
        name="FastAPI Project Generator",
        version="2.0.0",
        domain="codegen",
        subdomain="generator",
        tags=["python", "project", "skeleton"],
        inputs={"project_name": {"type": "string"}},
        outputs={"main.py": "python", "Dockerfile": "dockerfile", "README.md": "markdown"},
        dependencies=[],
        generator=gen_fastapi_project,
    ))

    REGISTRY.register(HEPComponent(
        id="gen.django.project",
        name="Django Project Generator",
        version="2.0.0",
        domain="codegen",
        subdomain="generator",
        tags=["python", "django", "skeleton"],
        inputs={"project_name": {"type": "string"}, "apps": {"type": "array"}},
        outputs={"manage.py": "text", "settings.py": "text", "apps/__init__.py": "python"},
        dependencies=[],
        generator=gen_django_project,
    ))

    REGISTRY.register(HEPComponent(
        id="gen.postgres.schema",
        name="PostgreSQL Schema Generator",
        version="2.0.0",
        domain="database",
        subdomain="schema",
        tags=["sql", "schema", "database"],
        inputs={"tables": {"type": "array"}},
        outputs={"schema.sql": "sql"},
        dependencies=[],
        generator=gen_postgres_schema,
    ))

    REGISTRY.register(HEPComponent(
        id="gen.dockerfile",
        name="Dockerfile Generator",
        version="2.0.0",
        domain="devops",
        subdomain="container",
        tags=["docker", "container", "devops"],
        inputs={"base_image": {"type": "string", "default": "python:3.12-slim"}, "port": {"type": "number", "default": 8000}},
        outputs={"Dockerfile": "docker", ".dockerignore": "text"},
        dependencies=[],
        generator=gen_dockerfile,
    ))

    REGISTRY.register(HEPComponent(
        id="gen.docker-compose",
        name="Docker Compose Generator",
        version="2.0.0",
        domain="devops",
        subdomain="orchestration",
        tags=["docker-compose", "orchestration", "deploy"],
        inputs={"services": {"type": "array"}},
        outputs={"docker-compose.yml": "yaml"},
        dependencies=[],
        generator=gen_docker_compose,
    ))

    REGISTRY.register(HEPComponent(
        id="gen.github-actions",
        name="GitHub Actions CI Generator",
        version="2.0.0",
        domain="devops",
        subdomain="pipeline",
        tags=["github-actions", "ci", "cd", "test"],
        inputs={"framework": {"type": "string"}, "test_cmd": {"type": "string", "default": "pytest"}},
        outputs={".github/workflows/ci.yml": "yaml"},
        dependencies=[],
        generator=gen_github_actions,
    ))

    REGISTRY.register(HEPComponent(
        id="gen.readme",
        name="README Generator",
        version="2.0.0",
        domain="documentation",
        subdomain="readme",
        tags=["markdown", "documentation"],
        inputs={"project_name": {"type": "string"}, "description": {"type": "string", "default": ""}},
        outputs={"README.md": "markdown"},
        dependencies=[],
        generator=gen_readme,
    ))

    # --------------------------------------------------------------------
    # Backend Service Templates
    # --------------------------------------------------------------------
    REGISTRY.register(HEPComponent(
        id="fastapi.project.templates.api",
        name="API Router Template",
        version="1.0.0",
        domain="backend",
        subdomain="template",
        tags=["api", "router"],
        inputs={"modules": {"type": "array"}},
        outputs={"api/router.py": "python"},
        dependencies=[],
    ))

    REGISTRY.register(HEPComponent(
        id="fastapi.project.templates.models",
        name="SQLAlchemy Models Template",
        version="1.0.0",
        domain="database",
        subdomain="models",
        tags=["model", "schema"],
        inputs={"model_names": {"type": "array"}},
        outputs={"models.py": "python"},
        dependencies=[],
    ))


register_defaults()

__all__ = ["HEPComponent", "HEPRegistry", "REGISTRY"]
