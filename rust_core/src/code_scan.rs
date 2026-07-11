// code_scan.rs — Fast code complexity analysis
// AST-free scanning using regex and line-counting heuristics.
// 50-100x faster than Python AST parsing for large codebases.

use pyo3::prelude::*;
use regex::Regex;
use std::collections::HashMap;

/// Scan a Python file for complexity hotspots without parsing AST.
#[pyfunction]
pub fn scan_complexity(source: &str) -> PyResult<HashMap<String, Vec<HashMap<String, String>>>> {
    let mut results: HashMap<String, Vec<HashMap<String, String>>> = HashMap::new();
    results.insert("functions".to_string(), Vec::new());
    
    let func_re = Regex::new(r"(?m)^[ \t]*(?:async[ \t]+)?def[ \t]+(\w+)").unwrap();
    let indent_re = Regex::new(r"(?m)^([ \t]+)(if|for|while|with|except|elif|else)\b").unwrap();
    let return_re = Regex::new(r"(?m)\breturn\b").unwrap();
    let loop_re = Regex::new(r"(?m)^[ \t]*(for|while)\b").unwrap();
    
    let lines: Vec<&str> = source.lines().collect();
    
    // Find function boundaries
    let mut funcs = Vec::new();
    for cap in func_re.captures_iter(source) {
        let name = cap[1].to_string();
        let start = cap.get(0).unwrap().start();
        // Count newlines before this position to get line number
        let line_no = source[..start].chars().filter(|&c| c == '\n').count() + 1;
        funcs.push((name, line_no, start));
    }
    
    // Add sentinel
    funcs.push(("__END__".to_string(), lines.len() + 1, source.len()));
    
    // Analyze each function
    for i in 0..funcs.len() - 1 {
        let (ref name, line_start, byte_start) = funcs[i];
        let (_, line_end, byte_end) = funcs[i + 1];
        
        let slice = &source[byte_start..byte_end.min(source.len())];
        let func_lines = slice.chars().filter(|&c| c == '\n').count() + 1;
        
        // Count control flow
        let indent_count = indent_re.captures_iter(slice).count();
        let loop_count = loop_re.captures_iter(slice).count();
        let return_count = return_re.captures_iter(slice).count();
        
        let complexity = 1 + indent_count;
        let hint = if complexity > 10 { "high_complexity" }
        else if complexity > 5 && func_lines > 50 { "long_function" }
        else if loop_count > 1 && loop_re.captures_iter(slice).count() > 1 { "nested_loops" }
        else { "" };
        
        if !hint.is_empty() {
            let mut info = HashMap::new();
            info.insert("name".to_string(), name.clone());
            info.insert("line_start".to_string(), line_start.to_string());
            info.insert("line_end".to_string(), line_end.to_string());
            info.insert("complexity".to_string(), complexity.to_string());
            info.insert("lines".to_string(), func_lines.to_string());
            info.insert("hint".to_string(), hint.to_string());
            info.insert("loops".to_string(), loop_count.to_string());
            info.insert("returns".to_string(), return_count.to_string());
            
            results.entry("functions".to_string())
                .or_default()
                .push(info);
        }
    }
    
    Ok(results)
}

/// Fast batch scan of multiple files.
#[pyfunction]
pub fn find_targets_fast(files: Vec<(String, String)>) -> PyResult<Vec<HashMap<String, String>>> {
    // files: Vec<(file_path, source_code)>
    let mut results = Vec::new();
    
    for (path, source) in files {
        let scan = scan_complexity(&source)?;
        if let Some(funcs) = scan.get("functions") {
            for f in funcs {
                let mut entry = f.clone();
                entry.insert("file".to_string(), path.clone());
                results.push(entry);
            }
        }
    }
    
    Ok(results)
}
