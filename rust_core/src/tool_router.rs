/// LAAP Tool Router — 工具调用路由引擎 (Rust)
///
/// 管理工具 Schema、路由调用、Schema 压缩。
/// 核心优化：工具定义不重复序列化，缓存 schema 字符串。
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// 工具分类
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ToolCategory {
    Core,
    Code,
    Web,
    System,
    Skill,
    Mcp,
}

impl ToolCategory {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Core => "core",
            Self::Code => "code",
            Self::Web => "web",
            Self::System => "system",
            Self::Skill => "skill",
            Self::Mcp => "mcp",
        }
    }
}

/// 精简工具定义
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolSchema {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub description: String,  // < 100 chars
    pub parameters: HashMap<String, serde_json::Value>,
    pub category: ToolCategory,
    /// 缓存过的 OpenAI 格式 schema 字符串
    #[serde(skip)]
    schema_cache: Option<String>,
}

#[pymethods]
impl ToolSchema {
    #[new]
    pub fn new(name: String, description: String, category: &str) -> Self {
        let cat = match category {
            "code" => ToolCategory::Code,
            "web" => ToolCategory::Web,
            "system" => ToolCategory::System,
            "skill" => ToolCategory::Skill,
            "mcp" => ToolCategory::Mcp,
            _ => ToolCategory::Core,
        };
        Self {
            name,
            description,
            parameters: HashMap::new(),
            category: cat,
            schema_cache: None,
        }
    }

    pub fn add_param(&mut self, name: &str, param_json: &str) {
        if let Ok(val) = serde_json::from_str(param_json) {
            self.parameters.insert(name.to_string(), val);
        }
    }

    /// 获取 OpenAI 格式的 schema 字符串（带缓存）
    pub fn openai_schema(&mut self) -> String {
        if let Some(cached) = &self.schema_cache {
            return cached.clone();
        }
        let schema = serde_json::json!({
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                }
            }
        });
        let s = schema.to_string();
        self.schema_cache = Some(s.clone());
        s
    }

    fn __repr__(&self) -> String {
        format!("{} [{:?}]", self.name, self.category)
    }
}

/// ToolRegistry — 工具注册中心
#[pyclass]
pub struct ToolRegistry {
    tools: HashMap<String, ToolSchema>,
    category_map: HashMap<String, Vec<String>>,
    loaded_categories: Vec<String>,
}

#[pymethods]
impl ToolRegistry {
    #[new]
    pub fn new() -> Self {
        Self {
            tools: HashMap::new(),
            category_map: HashMap::new(),
            loaded_categories: Vec::new(),
        }
    }

    /// 注册工具
    pub fn register(&mut self, tool: ToolSchema) {
        let name = tool.name.clone();
        let cat = tool.category.as_str().to_string();
        self.tools.insert(name.clone(), tool);
        self.category_map
            .entry(cat)
            .or_insert_with(Vec::new)
            .push(name);
    }

    /// 按类别加载工具，返回 OpenAI 格式的 schema 列表
    pub fn load_category(&mut self, category: &str) -> Vec<String> {
        let mut schemas = Vec::new();
        if let Some(names) = self.category_map.get(category) {
            for name in names {
                if let Some(tool) = self.tools.get_mut(name) {
                    schemas.push(tool.openai_schema());
                }
            }
        }
        if !self.loaded_categories.contains(&category.to_string()) {
            self.loaded_categories.push(category.to_string());
        }
        schemas
    }

    /// 获取已加载的工具数
    pub fn loaded_count(&self) -> usize {
        self.loaded_categories
            .iter()
            .flat_map(|cat| self.category_map.get(cat))
            .map(|v| v.len())
            .sum()
    }

    /// 总注册工具数
    pub fn total_count(&self) -> usize {
        self.tools.len()
    }

    /// 估算已加载工具的 schema token 数
    pub fn estimated_tool_tokens(&self) -> u32 {
        self.loaded_categories
            .iter()
            .flat_map(|cat| self.category_map.get(cat))
            .flatten()
            .filter_map(|name| self.tools.get(name))
            .map(|t| {
                let s = if let Some(cached) = &t.schema_cache {
                    cached.clone()
                } else {
                    // 粗略估算
                    format!("{} {}", t.name, t.description)
                };
                (s.len() / 4) as u32
            })
            .sum()
    }

    fn __repr__(&self) -> String {
        format!(
            "TR|loaded={}/{} cats={:?} tok≈{}",
            self.loaded_count(),
            self.total_count(),
            self.loaded_categories,
            self.estimated_tool_tokens(),
        )
    }
}

/// 工具调用结果
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResult {
    #[pyo3(get)]
    pub success: bool,
    #[pyo3(get)]
    pub message: String,
    #[pyo3(get)]
    pub token_cost: u32,
    pub data: Option<serde_json::Value>,
}

#[pymethods]
impl ToolResult {
    #[new]
    pub fn new(success: bool, message: String) -> Self {
        Self {
            success,
            message,
            token_cost: 0,
            data: None,
        }
    }

    fn __repr__(&self) -> String {
        if self.success {
            format!("✅ {}", self.message)
        } else {
            format!("❌ {}", self.message)
        }
    }
}
