// LAAP Dev Harness — Rust Native Acceleration Core
// PyO3 绑定：导出 TokenBudget, ToolRegistry, Provider, UiaCache 给 Python

pub mod cua;
mod token_budget;
mod tool_router;
mod provider;

use pyo3::prelude::*;
use pyo3::types::PyBytes;

/// LAAP Harness — Python 绑定
#[pymodule]
fn laap_harness(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<token_budget::TokenBudget>()?;
    m.add_class::<tool_router::ToolSchema>()?;
    m.add_class::<tool_router::ToolRegistry>()?;
    m.add_class::<tool_router::ToolResult>()?;
    m.add_class::<cua::UiaCache>()?;
    m.add_class::<cua::CUAAction>()?;
    Ok(())
}

/// 估算文本的 token 数
#[pyfunction]
fn count_tokens(text: &str) -> usize {
    text.len() / 4
}
