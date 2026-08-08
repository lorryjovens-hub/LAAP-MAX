/// LAAP Provider — LLM Provider 抽象层 (Rust)
///
/// 支持 DeepSeek / OpenAI 兼容接口。
/// 核心优化：自动跟踪 prompt cache 命中率。
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

/// 单次 LLM 调用的结果
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LLMResult {
    #[pyo3(get)]
    pub content: String,
    #[pyo3(get)]
    pub finish_reason: String,
    #[pyo3(get)]
    pub prompt_tokens: u32,
    #[pyo3(get)]
    pub completion_tokens: u32,
    #[pyo3(get)]
    pub total_tokens: u32,
    #[pyo3(get)]
    pub cache_hit_tokens: u32,
    #[pyo3(get)]
    pub error: String,
}

#[pymethods]
impl LLMResult {
    #[new]
    pub fn new(content: String) -> Self {
        Self {
            content,
            finish_reason: String::new(),
            prompt_tokens: 0,
            completion_tokens: 0,
            total_tokens: 0,
            cache_hit_tokens: 0,
            error: String::new(),
        }
    }

    pub fn cache_hit_rate(&self) -> f64 {
        if self.prompt_tokens == 0 {
            return 0.0;
        }
        self.cache_hit_tokens as f64 / self.prompt_tokens as f64
    }

    fn __repr__(&self) -> String {
        if !self.error.is_empty() {
            return format!("❌ {}", self.error);
        }
        let cache_pct = self.cache_hit_rate() * 100.0;
        let content_preview = if self.content.len() > 40 {
            format!("{}...", &self.content[..40])
        } else {
            self.content.clone()
        };
        format!(
            "OK T:{}/{} cache:{:.0}% | {}",
            self.completion_tokens, self.total_tokens, cache_pct, content_preview
        )
    }
}

/// 构建聊天请求
#[derive(Debug, Serialize)]
struct ChatRequest {
    model: String,
    messages: Vec<Message>,
    temperature: f64,
    max_tokens: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    tools: Option<Vec<serde_json::Value>>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Message {
    role: String,
    content: String,
}

/// 解析 DeepSeek API 响应
#[derive(Debug, Deserialize)]
struct ChatResponse {
    choices: Vec<Choice>,
    usage: Option<Usage>,
}

#[derive(Debug, Deserialize)]
struct Choice {
    message: ChoiceMessage,
    finish_reason: String,
}

#[derive(Debug, Deserialize)]
struct ChoiceMessage {
    content: Option<String>,
}

#[derive(Debug, Deserialize)]
struct Usage {
    prompt_tokens: Option<u32>,
    completion_tokens: Option<u32>,
    total_tokens: Option<u32>,
    #[serde(default)]
    prompt_cache_hit_tokens: Option<u32>,
}

/// Provider 客户端
#[pyclass]
pub struct Provider {
    api_base: String,
    api_key: String,
    model: String,
    client: Option<reqwest::blocking::Client>,
}

#[pymethods]
impl Provider {
    #[new]
    pub fn new(api_base: String, api_key: String, model: String) -> Self {
        let client = reqwest::blocking::Client::builder()
            .timeout(std::time::Duration::from_secs(120))
            .build()
            .ok();
        Self {
            api_base,
            api_key,
            model,
            client,
        }
    }

    /// 发送聊天请求（阻塞）
    pub fn chat(
        &self,
        messages_json: &str,
        tools_json: Option<&str>,
        temperature: Option<f64>,
    ) -> LLMResult {
        let client = match &self.client {
            Some(c) => c,
            None => return LLMResult::new("Provider client not initialized".to_string()),
        };

        let messages: Vec<Message> = match serde_json::from_str(messages_json) {
            Ok(msgs) => msgs,
            Err(e) => return LLMResult::new(format!("Invalid messages JSON: {}", e)),
        };

        let tools: Option<Vec<serde_json::Value>> = match tools_json {
            Some(json_str) => serde_json::from_str(json_str).ok(),
            None => None,
        };

        let request = ChatRequest {
            model: self.model.clone(),
            messages,
            temperature: temperature.unwrap_or(0.3),
            max_tokens: 4096,
            tools,
        };

        let body = match serde_json::to_string(&request) {
            Ok(b) => b,
            Err(e) => return LLMResult::new(format!("Serialization error: {}", e)),
        };

        let url = format!("{}/chat/completions", self.api_base.trim_end_matches('/'));

        let response = match client
            .post(&url)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .body(body)
            .send()
        {
            Ok(r) => r,
            Err(e) => return LLMResult::new(format!("HTTP error: {}", e)),
        };

        let status = response.status();
        if !status.is_success() {
            let text = response.text().unwrap_or_default();
            return LLMResult::new(format!("API error {}: {}", status, text));
        }

        let text = match response.text() {
            Ok(t) => t,
            Err(e) => return LLMResult::new(format!("Read error: {}", e)),
        };

        let chat_resp: ChatResponse = match serde_json::from_str(&text) {
            Ok(r) => r,
            Err(e) => return LLMResult::new(format!("Parse error: {} | body: {}", e, &text[..200.min(text.len())])),
        };

        let choice = match chat_resp.choices.into_iter().next() {
            Some(c) => c,
            None => return LLMResult::new("No choices in response".to_string()),
        };

        let mut result = LLMResult::new(choice.message.content.unwrap_or_default());
        result.finish_reason = choice.finish_reason;

        if let Some(usage) = chat_resp.usage {
            result.prompt_tokens = usage.prompt_tokens.unwrap_or(0);
            result.completion_tokens = usage.completion_tokens.unwrap_or(0);
            result.total_tokens = usage.total_tokens.unwrap_or(0);
            result.cache_hit_tokens = usage.prompt_cache_hit_tokens.unwrap_or(0);
        }

        result
    }

    fn __repr__(&self) -> String {
        format!("Provider({}@{})", self.model, self.api_base)
    }
}

/// 估算 token 的 Python 绑定
#[pyfunction]
pub fn estimate_tokens_py(text: &str) -> u32 {
    super::token_budget::estimate_tokens(text)
}
