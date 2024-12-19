use pyo3::prelude::*;
use pyo3::types::PyDict;
use crate::engine::{Engine, Rule};
use crate::lang::Condition;

#[pyclass]
pub struct WebSocketPlugin {}

#[pymethods]
impl WebSocketPlugin {
    #[new]
    pub fn new() -> Self {
        WebSocketPlugin {}
    }

    pub fn register_rules(&self, engine: &mut Engine) {
        let condition = Condition::new(Box::new(|context: &PyDict| {
            context.get_item("type").unwrap().extract::<String>().unwrap() == "greeting"
        }));

        let rule = Rule::new("GreetingRule".to_string(), condition, 1);
        Engine.add_rule(rule);
    }
}
