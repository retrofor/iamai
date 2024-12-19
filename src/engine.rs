use pyo3::prelude::*;
use pyo3::types::PyDict;
use crate::lang::Condition;
use crate::plugin::Plugin;

#[pyclass]
pub struct Rule {
    name: String,
    condition: Condition,
    priority: i32,
}

#[pymethods]
impl Rule {
    #[new]
    fn new(name: String, condition: Condition, priority: i32) -> Self {
        Rule { name, condition, priority }
    }

    fn evaluate(&self, context: &PyDict) -> bool {
        self.condition.evaluate(context)
    }

    fn execute(&self, context: &PyDict) {
        // 执行规则的 action，通常是某些变更或通知
    }
}

#[pyclass]
pub struct Engine {
    rules: Vec<Rule>,
}

#[pymethods]
impl Engine {
    #[new]
    pub fn new(plugins: Vec<Box<dyn Plugin>>) -> Self {
        let mut engine = Engine { rules: Vec::new() };
        for plugin in plugins {
            plugin.register_rules(&mut engine);
        }
        engine
    }

    fn add_rule(&mut self, rule: Rule) {
        self.rules.push(rule);
        self.rules.sort_by(|a, b| b.priority.cmp(&a.priority)); // 按照优先级排序
    }

    pub fn process(&self, context: &PyDict) {
        for rule in &self.rules {
            if rule.evaluate(context) {
                rule.execute(context);
            }
        }
    }

    pub fn run(&self, host: String, port: u16) {
        // 启动 WebSocket 或其他服务
        println!("Engine running at ws://{}:{}", host, port);
    }
}
