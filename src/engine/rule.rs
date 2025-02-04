use pyo3::prelude::*;

#[pyclass]
struct Rule {
    condition: PyObject,
    action: PyObject,
    priority: i32,
}
