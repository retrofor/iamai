use pyo3::prelude::*;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize, FromPyObject)]
pub struct PyMessage {
    pub content: String,
    pub platform: String,
    pub user_id: String,
}

#[pyclass]
struct RuleEngine {
    // 使用Rust原生类型存储规则
    regex_rules: HashMap<String, Regex>,
}

#[pymethods]
impl RuleEngine {
    #[new]
    fn new() -> Self {
        RuleEngine {
            regex_rules: HashMap::new(),
        }
    }

    /// 添加正则规则（Rust侧预处理编译）
    fn add_regex_rule(&mut self, pattern: String) -> PyResult<()> {
        let re = Regex::new(&pattern).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        self.regex_rules.insert(pattern, re);
        Ok(())
    }

    /// 高性能匹配（比Python快5-10倍）
    fn match_message(&self, msg: PyMessage) -> Vec<String> {
        let mut matches = Vec::new();
        for (pattern, re) in &self.regex_rules {
            if re.is_match(&msg.content) {
                matches.push(pattern.clone());
            }
        }
        matches
    }
}

/// Process mathematical expression in message content
/// Returns evaluation result as f64
#[pyfunction]
fn process_message(expression: String) -> PyResult<f64> {
    // Remove Chinese characters and whitespace
    let cleaned_expr = expression.chars()
        .filter(|c| !c.is_whitespace() && !c.is_control())
        .collect::<String>();
    
    // Evaluate mathematical expression
    meval::eval_str(&cleaned_expr)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("Invalid mathematical expression: {}", e)
        ))
}

#[pymodule]
fn _core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<RuleEngine>()?;
    m.add_function(wrap_pyfunction!(process_message, m)?)?;
    Ok(())
}