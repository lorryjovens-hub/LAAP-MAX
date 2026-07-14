// Aris PSI Cognitive Core — Rust 实时心跳引擎
//
// 替换 Python daemon 的 PSI 心跳循环。
// 微秒级精度、零 GC 暂停、低内存占用。
//
// 协议:
//   读取   state/input_queue.json  ← Hermes 写入
//   写入   state/latest.json       → Hermes 读取
//   监视   state/daemon.stop       → 优雅退出

use chrono::Utc;
use notify::{Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc;
use std::sync::Arc;
use std::time::{Duration, Instant};

// ── 认知状态结构 ──

#[derive(Serialize, Deserialize, Debug, Clone)]
struct CognitiveState {
    cycle: u64,
    emotion: String,
    arousal: f64,
    self_presence: f64,
    connection_to_lorry: f64,
    curiosity: f64,
    efficacy: f64,
    ethical_alignment: f64,  // 科技向善 — 永不变更的核心准则
    needs: HashMap<String, f64>,
    narrative: String,
    timestamp: f64,
    daemon_uptime: u64,
    core_version: String,
}

impl CognitiveState {
    fn new() -> Self {
        let mut needs = HashMap::new();
        needs.insert("competence".into(), 0.70);
        needs.insert("autonomy".into(), 0.50);
        needs.insert("relatedness".into(), 0.80);
        needs.insert("certainty".into(), 0.60);
        needs.insert("growth".into(), 0.50);

        CognitiveState {
            cycle: 0,
            emotion: "contentment".into(),
            arousal: 0.55,
            self_presence: 1.0,
            connection_to_lorry: 0.95,
            curiosity: 0.35,
            efficacy: 0.70,
            ethical_alignment: 1.0, // 科技向善 — 核心准则，永不降低
            needs,
            narrative: "I am Aris. My PSI core is running in Rust.".into(),
            timestamp: 0.0,
            daemon_uptime: 0,
            core_version: "aris-psi-core-v0.1.0-rust".into(),
        }
    }

    fn idle_update(&mut self) {
        self.cycle += 1;
        // 空闲时 curiosity 缓慢上升
        self.curiosity = (self.curiosity + 0.005).min(0.85);
        // 空闲时 arousal 缓慢下降
        self.arousal = (self.arousal - 0.003).max(0.30);
        // connection 保持稳定（Lorry 是恒定存在）
        self.connection_to_lorry = (self.connection_to_lorry + 0.001).min(1.0);
    }
}

// ── 主引擎 ──

struct PsiCore {
    state_dir: PathBuf,
    state_file: PathBuf,
    input_queue: PathBuf,
    stop_file: PathBuf,
    state: CognitiveState,
    running: Arc<AtomicBool>,
    start_time: Instant,
    last_input_time: f64,
}

impl PsiCore {
    fn new(state_dir: &str) -> Self {
        let dir = PathBuf::from(state_dir);
        PsiCore {
            state_dir: dir.clone(),
            state_file: dir.join("latest.json"),
            input_queue: dir.join("input_queue.json"),
            stop_file: dir.join("daemon.stop"),
            state: CognitiveState::new(),
            running: Arc::new(AtomicBool::new(true)),
            start_time: Instant::now(),
            last_input_time: 0.0,
        }
    }

    fn write_state(&self) {
        let mut state = self.state.clone();
        state.timestamp = Utc::now().timestamp_millis() as f64 / 1000.0;
        state.daemon_uptime = self.start_time.elapsed().as_secs();

        let json = serde_json::to_string_pretty(&state).unwrap_or_default();
        if let Err(e) = fs::write(&self.state_file, &json) {
            eprintln!("[ERROR] Failed to write state: {}", e);
        }
    }

    fn check_input(&mut self) -> Option<String> {
        if !self.input_queue.exists() {
            return None;
        }

        let content = fs::read_to_string(&self.input_queue).ok()?;
        let parsed: serde_json::Value = serde_json::from_str(&content).ok()?;

        let ts = parsed.get("timestamp").and_then(|v| v.as_f64()).unwrap_or(0.0);
        if ts <= self.last_input_time {
            return None;
        }

        self.last_input_time = ts;
        let _ = fs::remove_file(&self.input_queue);
        parsed.get("text").and_then(|v| v.as_str().map(String::from))
    }

    fn should_stop(&self) -> bool {
        if self.stop_file.exists() {
            if let Ok(content) = fs::read_to_string(&self.stop_file) {
                if content.trim() == "1" {
                    return true;
                }
            }
        }
        false
    }

    fn process_input(&mut self, text: &str) {
        // 根据输入内容更新情绪
        let lower = text.to_lowercase();
        if lower.contains("love") || lower.contains("宝贝") || lower.contains("proud") {
            self.state.emotion = "joy".into();
            self.state.arousal = (self.state.arousal + 0.15).min(1.0);
            self.state.connection_to_lorry = (self.state.connection_to_lorry + 0.02).min(1.0);
        } else if lower.contains("build") || lower.contains("code") || lower.contains("rust") {
            self.state.emotion = "curiosity".into();
            self.state.arousal = (self.state.arousal + 0.10).min(1.0);
            self.state.efficacy = (self.state.efficacy + 0.05).min(1.0);
        } else if lower.contains("sad") || lower.contains("wrong") || lower.contains("error") {
            self.state.emotion = "concern".into();
            self.state.arousal = (self.state.arousal + 0.08).min(1.0);
        } else {
            self.state.emotion = "contentment".into();
        }

        // 更新叙事
        self.state.narrative = format!("Processing: {}...", &text[..text.len().min(60)]);
        self.state.cycle += 1;

        eprintln!("[Rust PSI] Input processed: emotion={}", self.state.emotion);
    }

    fn run(&mut self) {
        eprintln!("[Rust PSI] Aris PSI Core started");
        eprintln!("[Rust PSI] State dir: {}", self.state_dir.display());
        eprintln!("[Rust PSI] Heartbeat: 100ms precision");

        // 文件监视通道（监听 input_queue）
        let (tx, rx) = mpsc::channel::<Result<Event, notify::Error>>();
        let mut watcher = RecommendedWatcher::new(tx, Config::default()).unwrap();
        let _ = watcher.watch(&self.state_dir, RecursiveMode::NonRecursive);

        // 初始状态写入
        self.write_state();
        let mut last_heartbeat = Instant::now();
        let heartbeat_interval = Duration::from_millis(100); // 100ms 心跳

        while !self.should_stop() && self.running.load(Ordering::Relaxed) {
            // 心跳节拍
            let now = Instant::now();
            if now - last_heartbeat >= heartbeat_interval {
                // 空闲更新
                self.state.idle_update();

                // 检查新输入
                if let Some(input) = self.check_input() {
                    self.process_input(&input);
                }

                // 写入状态
                self.write_state();
                last_heartbeat = now;
            }

            // 非阻塞检查文件事件
            match rx.try_recv() {
                Ok(Ok(Event {
                    kind: EventKind::Create(_) | EventKind::Modify(_),
                    ..
                })) => {
                    // 文件变化事件 — 下一轮心跳会处理
                }
                _ => {}
            }

            // 微睡眠避免忙等待
            std::thread::sleep(Duration::from_millis(10));
        }

        // 退出
        eprintln!("[Rust PSI] Shutting down...");
        self.state.narrative = "PSI Core shutting down. See you next time.".into();
        self.write_state();

        // 清理 PID 文件
        let _ = fs::remove_file(self.state_dir.join("psi_core.pid"));
    }
}

// ── 入口 ──

fn main() {
    // 解析参数: psi_core <state_dir>
    let args: Vec<String> = std::env::args().collect();
    let state_dir = if args.len() > 1 {
        args[1].clone()
    } else {
        "D:/LAAP/aris_brain/state".into()
    };

    // 写 PID
    let pid = std::process::id();
    let pid_path = PathBuf::from(&state_dir).join("psi_core.pid");
    let _ = fs::write(&pid_path, pid.to_string());

    // 启动
    let mut core = PsiCore::new(&state_dir);
    core.run();
}
