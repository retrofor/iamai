use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3::wrap_pymodule;

pub mod engine;
pub mod plugin;
pub mod mapper;
pub mod lang;


use crate::engine::Engine;
use crate::plugin::WebSocketPlugin;

#[pymodule]
fn my_rust_module(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Engine>()?;
    m.add_function(wrap_pyfunction!(run_engine, m)?)?;
    Ok(())
}

#[pyfunction]
fn run_engine(py: Python, host: String, port: u16) -> PyResult<()> {
    let engine = Engine::new(vec![WebSocketPlugin::new()]);
    engine.run(host, port);
    Ok(())
}


#[pymodule]
fn _core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_submodule(wrap_pymodule!(my_rust_module, m)?)?;
    m.add_function(wrap_pyfunction!(run_engine, m)?)?;
    Ok(())
}
