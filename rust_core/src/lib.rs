// LAAP AGI — Rust Native Acceleration Core
// PyO3 bindings for Python interop
//
// Modules:
//   world_graph  — Accelerated entity/relation graph operations
//   code_scan    — Fast AST-free code complexity analysis
//   vector_ops   — SIMD-accelerated vector similarity
//   pattern_match — Regex + Aho-Corasick pattern scanning

use pyo3::prelude::*;

mod world_graph;
mod code_scan;
mod vector_ops;
mod pattern_match;

/// LAAP Core — main Python module
#[pymodule]
fn laap_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // World graph acceleration
    m.add_class::<world_graph::FastEntityGraph>()?;
    m.add_function(wrap_pyfunction!(world_graph::find_related_fast, m)?)?;
    m.add_function(wrap_pyfunction!(world_graph::topological_sort_fast, m)?)?;

    // Code analysis acceleration
    m.add_function(wrap_pyfunction!(code_scan::scan_complexity, m)?)?;
    m.add_function(wrap_pyfunction!(code_scan::find_targets_fast, m)?)?;

    // Vector operations
    m.add_function(wrap_pyfunction!(vector_ops::cosine_similarity_batch, m)?)?;
    m.add_function(wrap_pyfunction!(vector_ops::top_k_similar, m)?)?;

    // Pattern matching
    m.add_function(wrap_pyfunction!(pattern_match::scan_threats_fast, m)?)?;
    m.add_function(wrap_pyfunction!(pattern_match::multi_pattern_match, m)?)?;

    // Version
    m.add("__version__", "0.1.0")?;
    m.add("__author__", "LAAP AGI Team")?;

    Ok(())
}
