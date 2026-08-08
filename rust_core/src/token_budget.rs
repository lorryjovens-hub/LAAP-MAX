/// LAAP Token Budget Engine — Token 预算引擎 (Rust)
///
/// 性能关键路径：每轮对话需在 < 1μs 内完成预算检查。
/// Python 层每轮调用一次，Rust 侧维护内部状态。
use pyo3::prelude::*;

/// TokenBudget — 线程安全的 Token 预算跟踪器
#[pyclass]
#[derive(Debug, Clone)]
pub struct TokenBudget {
    /// 总预算上限
    budget: u32,
    /// 已消耗 token
    spent: u32,
    /// 历史记录（保留最近 100 条）
    history: Vec<HistoryEntry>,
    /// 起始时间
    started_at: f64,
}

#[derive(Debug, Clone, serde::Serialize)]
struct HistoryEntry {
    tokens: u32,
    source: String,
    timestamp: f64,
}

#[pymethods]
impl TokenBudget {
    #[new]
    pub fn new(budget: Option<u32>) -> Self {
        Self {
            budget: budget.unwrap_or(800),
            spent: 0,
            history: Vec::with_capacity(100),
            started_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs_f64(),
        }
    }

    /// 扣除 token，返回剩余
    pub fn charge(&mut self, tokens: u32, source: &str) -> u32 {
        self.spent += tokens;
        if self.history.len() < 100 {
            self.history.push(HistoryEntry {
                tokens,
                source: source.to_string(),
                timestamp: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_secs_f64(),
            });
        }
        self.remaining()
    }

    /// 剩余 token
    pub fn remaining(&self) -> u32 {
        self.budget.saturating_sub(self.spent)
    }

    /// 是否已耗尽
    pub fn is_exhausted(&self) -> bool {
        self.spent >= self.budget
    }

    /// 已消耗
    pub fn spent(&self) -> u32 {
        self.spent
    }

    /// 预算总额
    pub fn budget(&self) -> u32 {
        self.budget
    }

    /// 使用率 (0.0 ~ 1.0)
    pub fn utilization(&self) -> f64 {
        if self.budget == 0 {
            return 0.0;
        }
        (self.spent as f64 / self.budget as f64).min(1.0)
    }

    fn __repr__(&self) -> String {
        format!("T:{}/{} {:.0}%", self.spent, self.budget, self.utilization() * 100.0)
    }

    /// 重置预算（新任务时调用）
    pub fn reset(&mut self, new_budget: Option<u32>) {
        self.budget = new_budget.unwrap_or(800);
        self.spent = 0;
        self.history.clear();
    }

    #[getter]
    pub fn summary(&self) -> String {
        let pct = (self.utilization() * 100.0) as u32;
        let bar_len = pct / 10;
        let bar = "\u{2588}".repeat(bar_len as usize) + &"\u{2591}".repeat(10 - bar_len as usize);
        format!("T:{}/{} {} {}%", self.spent, self.budget, bar, pct)
    }
}

/// 估算文本的 token 数（快速近似，中文按 1.5 char/token）
pub fn estimate_tokens(text: &str) -> u32 {
    let mut tokens = 0u32;
    for ch in text.chars() {
        if ch >= '\u{4e00}' && ch <= '\u{9fff}' {
            tokens += 2; // 中文 ~2 chars/token
        } else if ch.is_ascii() {
            tokens += 1; // 英文/数字 ~4 chars/token
        } else {
            tokens += 2; // 其他
        }
    }
    (tokens / 4).max(1)
}

#[pyfunction]
pub fn count_tokens(text: &str) -> u32 {
    estimate_tokens(text)
}
