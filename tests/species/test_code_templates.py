"""Tests for laap.species.code_templates (Task C3)."""
from __future__ import annotations

import os
import tempfile

import pytest

from laap.species.code_templates.builtin import builtin_templates, register_builtins
from laap.species.code_templates.registry import CodeTemplate, TemplateRegistry


@pytest.fixture
def temp_registry():
    """Fresh TemplateRegistry backed by a temp JSON file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "code_templates.json")
        yield TemplateRegistry(path=path)


class TestCodeTemplate:
    def test_register_and_get_template(self, temp_registry):
        tpl = CodeTemplate(
            template_id="demo_add",
            name="Add",
            description="Add two numbers",
            language="python",
            code="def add(a, b):\n    return a + b\n",
            metadata={"scenario": "math"},
        )
        sid = temp_registry.register(tpl)
        assert sid == tpl.species_id
        assert sid.startswith("species_")

        got = temp_registry.get(sid)
        assert got is not None
        assert got.template_id == "demo_add"
        assert got.language == "python"
        assert "def add" in got.code

        # Persistence: reload from disk and the template should still be there.
        reloaded = TemplateRegistry(path=temp_registry.path)
        assert reloaded.get(sid) is not None
        assert reloaded.get(sid).template_id == "demo_add"

    def test_search_by_language(self, temp_registry):
        py_tpl = CodeTemplate(
            template_id="py_one",
            name="Py One",
            description="",
            language="python",
            code="x = 1\n",
        )
        js_tpl = CodeTemplate(
            template_id="js_one",
            name="JS One",
            description="",
            language="javascript",
            code="const x = 1;\n",
        )
        temp_registry.register(py_tpl)
        temp_registry.register(js_tpl)

        py_results = temp_registry.search(language="python")
        assert len(py_results) == 1
        assert py_results[0].language == "python"

        all_results = temp_registry.list_all()
        assert len(all_results) == 2

        # Search is case-insensitive.
        assert len(temp_registry.search(language="PYTHON")) == 1

    def test_builtin_templates_loaded(self, temp_registry):
        # Sanity: builtin_templates() returns exactly 3 templates.
        templates = builtin_templates()
        assert len(templates) == 3

        ids = {t.template_id for t in templates}
        assert ids == {
            "python_hello_world",
            "python_dataclass_template",
            "python_async_task_template",
        }

        # Each builtin is a valid Python source.
        import ast as _ast
        for t in templates:
            assert t.language == "python"
            _ast.parse(t.code)
            assert "scenario" in t.metadata

        # Register them and confirm they survive a reload.
        register_builtins(temp_registry)
        assert len(temp_registry.list_all()) == 3

        reloaded = TemplateRegistry(path=temp_registry.path)
        assert len(reloaded.list_all()) == 3
        assert {t.template_id for t in reloaded.list_all()} == ids
