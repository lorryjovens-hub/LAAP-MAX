"""Tests for laap.domain_sdk.harness_function — registry and decorator."""

from __future__ import annotations

import asyncio

import pytest

from laap.domain_sdk.harness_function import (
    HarnessFunction,
    HarnessFunctionRegistry,
    harness_function,
    _infer_schema,
    _python_type_to_json_type,
)


# ── HarnessFunction dataclass tests ────────────────────────────────


class TestHarnessFunctionDataclass:
    def test_domain_extracted_from_name(self):
        hf = HarnessFunction(
            name="finquant.indicators.compute",
            fn=async_func(lambda: None),
        )
        assert hf.domain == "finquant"
        assert hf.category == "indicators"

    def test_explicit_domain_not_overridden(self):
        hf = HarnessFunction(
            name="custom.name",
            fn=async_func(lambda: None),
            domain="explicit_domain",
        )
        assert hf.domain == "explicit_domain"

    def test_to_tool_schema(self):
        hf = HarnessFunction(
            name="finquant.data.get",
            fn=async_func(lambda: None),
            description="Get data",
            schema={"type": "object", "properties": {}},
        )
        schema = hf.to_tool_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "finquant.data.get"
        assert schema["function"]["description"] == "Get data"


# ── HarnessFunctionRegistry tests ──────────────────────────────────


class TestHarnessFunctionRegistry:
    def setup_method(self):
        self.registry = HarnessFunctionRegistry()

    def test_register_and_get(self):
        async def my_func(x: int) -> int:
            return x * 2

        self.registry.register("test.math.double", my_func)
        hf = self.registry.get("test.math.double")
        assert hf is not None
        assert hf.name == "test.math.double"
        assert hf.domain == "test"

    def test_register_non_async_wraps_in_shim(self):
        def sync_func(x: int) -> int:
            return x + 1

        self.registry.register("test.math.add", sync_func)
        hf = self.registry.get("test.math.add")
        assert asyncio.iscoroutinefunction(hf.fn)

    def test_decorator_registration(self):
        @self.registry.register("test.strats.momentum", zero_token=True)
        async def momentum(data, period=20):
            return {"signal": "long"}

        hf = self.registry.get("test.strats.momentum")
        assert hf is not None
        assert hf.zero_token is True

    def test_harness_alias_decorator(self):
        @self.registry.harness("test.strats.reversion")
        async def reversion(data):
            return {"signal": "short"}

        assert "test.strats.reversion" in self.registry

    def test_duplicate_registration_silently_skipped(self):
        async def func_a(x):
            return "a"

        async def func_b(x):
            return "b"

        self.registry.register("test.dup", func_a)
        self.registry.register("test.dup", func_b)  # should skip

        hf = self.registry.get("test.dup")
        result = asyncio.run(hf.fn(x=1))
        assert result == "a"  # original kept

    def test_overwrite_registration(self):
        async def func_a(x):
            return "a"

        async def func_b(x):
            return "b"

        self.registry.register("test.ow", func_a)
        self.registry.register("test.ow", func_b, overwrite=True)

        hf = self.registry.get("test.ow")
        result = asyncio.run(hf.fn(x=1))
        assert result == "b"

    @pytest.mark.asyncio
    async def test_invoke(self):
        async def add(a: int, b: int) -> int:
            return a + b

        self.registry.register("test.math.add", add)
        result = await self.registry.invoke("test.math.add", a=3, b=4)
        assert result == 7

    @pytest.mark.asyncio
    async def test_invoke_missing_function_raises(self):
        with pytest.raises(KeyError):
            await self.registry.invoke("nonexistent.fn")

    @pytest.mark.asyncio
    async def test_invoke_missing_required_param(self):
        async def func(a: int, b: int):
            return a + b

        self.registry.register("test.required", func)
        with pytest.raises(TypeError, match="missing required"):
            await self.registry.invoke("test.required", a=1)

    def test_invoke_sync(self):
        async def multiply(x: int, y: int) -> int:
            return x * y

        self.registry.register("test.math.mul", multiply)
        result = self.registry.invoke_sync("test.math.mul", x=5, y=6)
        assert result == 30

    def test_list_filter_by_domain(self):
        async def f1():
            pass

        async def f2():
            pass

        self.registry.register("finquant.data.get", f1)
        self.registry.register("legal.search.case", f2)

        finquant_funcs = self.registry.list(domain="finquant")
        assert len(finquant_funcs) == 1
        assert finquant_funcs[0].name == "finquant.data.get"

    def test_list_filter_by_category(self):
        async def f1():
            pass

        async def f2():
            pass

        self.registry.register("finquant.data.get", f1)
        self.registry.register("finquant.risk.var", f2)

        data_funcs = self.registry.list(category="data")
        assert len(data_funcs) == 1
        assert data_funcs[0].name == "finquant.data.get"

    def test_list_names(self):
        async def f1():
            pass

        self.registry.register("a.b.c", f1)
        names = self.registry.list_names()
        assert "a.b.c" in names

    def test_to_tool_schemas(self):
        async def f1(x: int):
            pass

        self.registry.register("test.fn", f1)
        schemas = self.registry.to_tool_schemas()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"

    def test_unregister(self):
        async def f():
            pass

        self.registry.register("test.rm", f)
        assert self.registry.unregister("test.rm") is True
        assert self.registry.get("test.rm") is None
        assert self.registry.unregister("test.rm") is False

    def test_clear(self):
        async def f():
            pass

        self.registry.register("test.a", f)
        self.registry.register("test.b", f)
        self.registry.clear()
        assert len(self.registry) == 0

    def test_contains(self):
        async def f():
            pass

        self.registry.register("test.contains", f)
        assert "test.contains" in self.registry
        assert "nonexistent" not in self.registry

    def test_domains_property(self):
        async def f():
            pass

        self.registry.register("finquant.a.b", f)
        self.registry.register("legal.a.b", f)
        assert "finquant" in self.registry.domains
        assert "legal" in self.registry.domains


# ── Module-level decorator tests ───────────────────────────────────


class TestHarnessFunctionDecorator:
    def test_decorator_attaches_metadata(self):
        @harness_function(
            name="finquant.data.get",
            description="Get financial data",
            zero_token=True,
        )
        async def get_data(symbols, start, end, interval="1d"):
            return {}

        assert get_data.__laap_harness_name__ == "finquant.data.get"
        assert get_data.__laap_harness_description__ == "Get financial data"
        assert get_data.__laap_harness_zero_token__ is True

    def test_registry_registers_decorated_function(self):
        registry = HarnessFunctionRegistry()

        @harness_function(name="test.decorated.fn", zero_token=True)
        async def my_fn(x: int) -> int:
            return x

        registry.register(
            name=my_fn.__laap_harness_name__,
            fn=my_fn,
            description=my_fn.__laap_harness_description__,
            schema=my_fn.__laap_harness_schema__,
            zero_token=my_fn.__laap_harness_zero_token__,
        )

        hf = registry.get("test.decorated.fn")
        assert hf is not None
        assert hf.zero_token is True


# ── Schema inference tests ─────────────────────────────────────────


class TestSchemaInference:
    def test_infer_basic_types(self):
        async def fn(a: str, b: int, c: float, d: bool):
            pass

        schema = _infer_schema(fn)
        props = schema["properties"]
        assert props["a"]["type"] == "string"
        assert props["b"]["type"] == "integer"
        assert props["c"]["type"] == "number"
        assert props["d"]["type"] == "boolean"

    def test_infer_required_vs_optional(self):
        async def fn(required_param: str, optional: int = 10):
            pass

        schema = _infer_schema(fn)
        assert "required_param" in schema["required"]
        assert "optional" not in schema["required"]
        assert schema["properties"]["optional"]["default"] == 10

    def test_python_type_to_json_type(self):
        assert _python_type_to_json_type(str) == "string"
        assert _python_type_to_json_type(int) == "integer"
        assert _python_type_to_json_type(float) == "number"
        assert _python_type_to_json_type(bool) == "boolean"
        assert _python_type_to_json_type(list) == "array"
        assert _python_type_to_json_type(dict) == "object"


# ── Helpers ────────────────────────────────────────────────────────


def async_func(fn):
    """Wrap a sync function as async."""
    async def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper
