use pyo3::prelude::*;
use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UIElement {
    pub index: u32,
    pub role: String,
    pub label: String,
    pub enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ElementDiff {
    pub added: Vec<UIElement>,
    pub removed: Vec<u32>,
    pub changed: Vec<UIElement>,
    pub snapshot_size: usize,
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct UiaCache {
    elements: HashMap<u32, UIElement>,
    next_index: u32,
}

#[pymethods]
impl UiaCache {
    #[new]
    pub fn new() -> Self { Self { elements: HashMap::new(), next_index: 1 } }

    pub fn diff(&mut self) -> PyResult<String> {
        let elements = vec![
            UIElement { index: 1, role: "window".into(), label: "命令行".into(), enabled: true },
            UIElement { index: 2, role: "edit".into(), label: "输入".into(), enabled: true },
        ];
        let mut diff = ElementDiff { added: Vec::new(), removed: Vec::new(), changed: Vec::new(), snapshot_size: 0 };
        for elem in &elements {
            if !self.elements.contains_key(&elem.index) { diff.added.push(elem.clone()); }
        }
        self.elements.clear();
        for elem in &elements { self.elements.insert(elem.index, elem.clone()); }
        diff.snapshot_size = self.elements.len();
        serde_json::to_string(&diff).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    pub fn size(&self) -> usize { self.elements.len() }

    fn __repr__(&self) -> String { format!("UiaCache|{}", self.elements.len()) }
}

#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CUAAction {
    pub action_type: String,
    pub element_index: u32,
    pub value: String,
}

#[pymethods]
impl CUAAction {
    #[new]
    pub fn new(action_type: String, element_index: u32, value: String) -> Self {
        Self { action_type, element_index, value }
    }

    pub fn execute(&self) -> PyResult<String> {
        Ok(format!("执行 {} 到元素 #{}: {}", self.action_type, self.element_index, self.value))
    }

    fn __repr__(&self) -> String { format!("{}->#{}", self.action_type, self.element_index) }
}
