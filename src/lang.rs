use pyo3::prelude::*;
use pyo3::types::PyDict;

#[pyclass]
pub struct Condition {
    func: Box<dyn Fn(&PyDict) -> bool>,
}

#[pymethods]
impl Condition {
    #[new]
    pub fn new(func: Box<dyn Fn(&PyDict) -> bool>) -> Self {
        Condition { func }
    }

    pub fn evaluate(&self, context: &PyDict) -> bool {
        (self.func)(context)
    }
}
