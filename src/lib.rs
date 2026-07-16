use std::collections::BTreeMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyModule;
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value, json};

static EVENT_COUNTER: AtomicU64 = AtomicU64::new(1);

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
struct Segment {
    kind: String,
    data: BTreeMap<String, Value>,
}

impl Segment {
    fn text(text: String) -> Self {
        let mut data = BTreeMap::new();
        data.insert("text".to_owned(), Value::String(text));
        Self {
            kind: "text".to_owned(),
            data,
        }
    }
}

#[pyclass(module = "iamai._core", name = "CoreMessage", skip_from_py_object)]
#[derive(Clone, Default)]
struct CoreMessage {
    segments: Vec<Segment>,
}

#[pymethods]
impl CoreMessage {
    #[new]
    fn new() -> Self {
        Self::default()
    }

    #[staticmethod]
    fn from_plain_text(text: String) -> Self {
        let mut message = Self::default();
        if !text.is_empty() {
            message.segments.push(Segment::text(text));
        }
        message
    }

    #[staticmethod]
    fn from_json(payload: &str) -> PyResult<Self> {
        let value = parse_json(payload)?;
        Self::from_value(value)
    }

    #[staticmethod]
    fn from_onebot11_json(payload: &str) -> PyResult<Self> {
        let value = parse_json(payload)?;
        Ok(Self {
            segments: parse_onebot11_segments(&value),
        })
    }

    fn push_text(&mut self, text: String) {
        if !text.is_empty() {
            self.segments.push(Segment::text(text));
        }
    }

    fn push(&mut self, kind: String, data_json: Option<&str>) -> PyResult<()> {
        let data = if let Some(raw) = data_json {
            parse_value_map(raw)?
        } else {
            BTreeMap::new()
        };
        self.segments.push(Segment { kind, data });
        Ok(())
    }

    fn extend_from_json(&mut self, payload: &str) -> PyResult<()> {
        let other = Self::from_json(payload)?;
        self.segments.extend(other.segments);
        Ok(())
    }

    fn plain_text(&self) -> String {
        self.segments
            .iter()
            .map(segment_plain_text)
            .collect::<String>()
    }

    fn render_text(&self) -> String {
        self.segments
            .iter()
            .map(segment_render_text)
            .collect::<String>()
    }

    fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(&self.segments_to_json())
            .map_err(|err| PyValueError::new_err(err.to_string()))
    }

    fn to_onebot11_json(&self) -> PyResult<String> {
        let value = Value::Array(
            self.segments
                .iter()
                .map(|segment| {
                    json!({
                        "type": segment.kind,
                        "data": stringified_data(&segment.data),
                    })
                })
                .collect(),
        );
        serde_json::to_string(&value).map_err(|err| PyValueError::new_err(err.to_string()))
    }

    fn copy(&self) -> Self {
        self.clone()
    }

    fn is_empty(&self) -> bool {
        self.segments.is_empty()
    }

    fn __len__(&self) -> usize {
        self.segments.len()
    }

    fn __repr__(&self) -> String {
        format!("CoreMessage({})", self.render_text())
    }

    fn __str__(&self) -> String {
        self.render_text()
    }
}

impl CoreMessage {
    fn from_value(value: Value) -> PyResult<Self> {
        let segments = match value {
            Value::Array(items) => items
                .iter()
                .map(segment_from_json)
                .collect::<PyResult<Vec<_>>>()?,
            Value::String(text) => vec![Segment::text(text)],
            _ => {
                return Err(PyValueError::new_err(
                    "message payload must be a JSON string or a JSON array",
                ));
            }
        };
        Ok(Self { segments })
    }

    fn segments_to_json(&self) -> Vec<Value> {
        self.segments
            .iter()
            .map(|segment| {
                json!({
                    "kind": segment.kind,
                    "data": segment.data,
                })
            })
            .collect()
    }
}

#[pyfunction]
fn next_event_id() -> String {
    next_event_id_inner()
}

#[pyfunction]
fn deep_merge_json(base_json: &str, overlay_json: &str) -> PyResult<String> {
    let mut base = parse_json(base_json)?;
    let overlay = parse_json(overlay_json)?;
    deep_merge(&mut base, overlay);
    serde_json::to_string(&base).map_err(|err| PyValueError::new_err(err.to_string()))
}

#[pyfunction]
#[pyo3(signature = (raw_json, adapter_name = "onebot11", platform = "qq"))]
fn normalize_onebot11_event(
    raw_json: &str,
    adapter_name: &str,
    platform: &str,
) -> PyResult<String> {
    let raw = parse_json(raw_json)?;
    let raw_object = raw
        .as_object()
        .ok_or_else(|| PyValueError::new_err("OneBot11 event payload must be a JSON object"))?;

    let post_type = get_string(raw_object, "post_type").unwrap_or_else(|| "unknown".to_owned());
    let detail_type = match post_type.as_str() {
        "message" => get_string(raw_object, "message_type"),
        "notice" => get_string(raw_object, "notice_type"),
        "request" => get_string(raw_object, "request_type"),
        "meta_event" => get_string(raw_object, "meta_event_type"),
        _ => None,
    };
    let sub_type = get_string(raw_object, "sub_type");
    let user_id = get_string(raw_object, "user_id");
    let group_id = get_string(raw_object, "group_id");
    let channel_id = group_id.clone().or_else(|| user_id.clone());
    let self_id = get_string(raw_object, "self_id");
    let message = raw_object
        .get("message")
        .map(parse_onebot11_segments)
        .unwrap_or_default();

    let normalized = json!({
        "id": next_event_id_inner(),
        "adapter": adapter_name,
        "platform": platform,
        "type": post_type,
        "detail_type": detail_type,
        "sub_type": sub_type,
        "user_id": user_id,
        "channel_id": channel_id,
        "guild_id": group_id,
        "self_id": self_id,
        "message": message
            .iter()
            .map(|segment| {
                json!({
                    "kind": segment.kind,
                    "data": segment.data,
                })
            })
            .collect::<Vec<_>>(),
        "raw": raw,
    });

    serde_json::to_string(&normalized).map_err(|err| PyValueError::new_err(err.to_string()))
}

#[pymodule]
#[pyo3(name = "_core")]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CoreMessage>()?;
    m.add_function(wrap_pyfunction!(deep_merge_json, m)?)?;
    m.add_function(wrap_pyfunction!(next_event_id, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_onebot11_event, m)?)?;
    Ok(())
}

fn next_event_id_inner() -> String {
    let millis = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis())
        .unwrap_or_default();
    let seq = EVENT_COUNTER.fetch_add(1, Ordering::Relaxed);
    format!("evt-{millis}-{seq}")
}

fn parse_json(payload: &str) -> PyResult<Value> {
    serde_json::from_str(payload).map_err(|err| PyValueError::new_err(err.to_string()))
}

fn parse_value_map(payload: &str) -> PyResult<BTreeMap<String, Value>> {
    let value = parse_json(payload)?;
    let object = value
        .as_object()
        .ok_or_else(|| PyValueError::new_err("segment data must be a JSON object"))?;
    Ok(object
        .iter()
        .map(|(key, value)| (key.clone(), value.clone()))
        .collect())
}

fn parse_onebot11_segments(value: &Value) -> Vec<Segment> {
    match value {
        Value::String(text) => vec![Segment::text(text.clone())],
        Value::Array(items) => items
            .iter()
            .filter_map(|item| onebot11_segment_from_json(item).ok())
            .collect(),
        _ => Vec::new(),
    }
}

fn segment_from_json(value: &Value) -> PyResult<Segment> {
    let object = value
        .as_object()
        .ok_or_else(|| PyValueError::new_err("segment entry must be a JSON object"))?;
    let kind = get_string(object, "kind")
        .or_else(|| get_string(object, "type"))
        .ok_or_else(|| PyValueError::new_err("segment requires 'kind' or 'type'"))?;
    let data = object
        .get("data")
        .and_then(Value::as_object)
        .map(|map| {
            map.iter()
                .map(|(key, value)| (key.clone(), value.clone()))
                .collect::<BTreeMap<_, _>>()
        })
        .unwrap_or_default();
    Ok(Segment { kind, data })
}

fn onebot11_segment_from_json(value: &Value) -> PyResult<Segment> {
    let object = value
        .as_object()
        .ok_or_else(|| PyValueError::new_err("OneBot11 segment entry must be a JSON object"))?;
    let kind = get_string(object, "type")
        .ok_or_else(|| PyValueError::new_err("OneBot11 segment requires 'type'"))?;
    let data = object
        .get("data")
        .and_then(Value::as_object)
        .map(|map| {
            map.iter()
                .map(|(key, value)| (key.clone(), Value::String(value_to_string(value))))
                .collect::<BTreeMap<_, _>>()
        })
        .unwrap_or_default();
    Ok(Segment { kind, data })
}

fn get_string(object: &Map<String, Value>, key: &str) -> Option<String> {
    object.get(key).map(value_to_string)
}

fn value_to_string(value: &Value) -> String {
    match value {
        Value::Null => String::new(),
        Value::String(text) => text.clone(),
        Value::Bool(flag) => flag.to_string(),
        Value::Number(number) => number.to_string(),
        other => other.to_string(),
    }
}

fn stringified_data(data: &BTreeMap<String, Value>) -> BTreeMap<String, String> {
    data.iter()
        .map(|(key, value)| (key.clone(), value_to_string(value)))
        .collect()
}

fn segment_plain_text(segment: &Segment) -> String {
    match segment.kind.as_str() {
        "text" => segment
            .data
            .get("text")
            .map(value_to_string)
            .unwrap_or_default(),
        "at" => segment
            .data
            .get("qq")
            .or_else(|| segment.data.get("user_id"))
            .map(|target| format!("@{}", value_to_string(target)))
            .unwrap_or_default(),
        _ => String::new(),
    }
}

fn segment_render_text(segment: &Segment) -> String {
    match segment.kind.as_str() {
        "text" => segment
            .data
            .get("text")
            .map(value_to_string)
            .unwrap_or_default(),
        "at" => segment
            .data
            .get("qq")
            .or_else(|| segment.data.get("user_id"))
            .map(|target| format!("@{}", value_to_string(target)))
            .unwrap_or_else(|| "@unknown".to_owned()),
        "image" => {
            let target = segment
                .data
                .get("file")
                .or_else(|| segment.data.get("url"))
                .map(value_to_string)
                .unwrap_or_else(|| "image".to_owned());
            format!("[image:{target}]")
        }
        other => format!("[{other}]"),
    }
}

fn deep_merge(base: &mut Value, overlay: Value) {
    match (base, overlay) {
        (Value::Object(base_map), Value::Object(overlay_map)) => {
            for (key, value) in overlay_map {
                if let Some(existing) = base_map.get_mut(&key) {
                    deep_merge(existing, value);
                } else {
                    base_map.insert(key, value);
                }
            }
        }
        (base_slot, overlay_value) => {
            *base_slot = overlay_value;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn deep_merge_preserves_nested_keys_and_replaces_arrays() {
        let mut base = json!({
            "runtime": {"log_level": "INFO", "plugins": ["echo"]},
            "enabled": true,
        });
        let overlay = json!({
            "runtime": {"plugins": ["react"], "hot_reload": false},
        });

        deep_merge(&mut base, overlay);

        assert_eq!(
            base,
            json!({
                "runtime": {
                    "log_level": "INFO",
                    "plugins": ["react"],
                    "hot_reload": false,
                },
                "enabled": true,
            })
        );
    }

    #[test]
    fn onebot_segments_preserve_plain_and_rendered_text() {
        let value = json!([
            {"type": "text", "data": {"text": "hello "}},
            {"type": "at", "data": {"qq": 42}},
            {"type": "image", "data": {"file": "photo.png"}},
        ]);

        let segments = parse_onebot11_segments(&value);
        let plain = segments.iter().map(segment_plain_text).collect::<String>();
        let rendered = segments.iter().map(segment_render_text).collect::<String>();

        assert_eq!(plain, "hello @42");
        assert_eq!(rendered, "hello @42[image:photo.png]");
    }

    #[test]
    fn segment_data_preserves_json_types_on_round_trip() {
        let payload = json!([
            {
                "kind": "custom",
                "data": {
                    "text": "legacy",
                    "count": 42,
                    "enabled": true,
                    "missing": null,
                    "nested": {"items": [1, false, null]},
                },
            },
        ]);

        let message = CoreMessage::from_value(payload.clone()).unwrap();

        assert_eq!(Value::Array(message.segments_to_json()), payload);
    }

    #[test]
    fn segment_data_preserves_arbitrary_precision_numbers() {
        let payload = serde_json::from_str::<Value>(
            r#"[{"kind":"custom","data":{"huge":10000000000000000000000000000000000000000}}]"#,
        )
        .unwrap();

        let message = CoreMessage::from_value(payload.clone()).unwrap();

        assert_eq!(Value::Array(message.segments_to_json()), payload);
    }

    #[test]
    fn onebot_segment_data_remains_string_normalized() {
        let payload = json!([
            {
                "type": "custom",
                "data": {
                    "text": "legacy",
                    "count": 42,
                    "enabled": true,
                    "missing": null,
                    "nested": {"items": [1, false, null]},
                },
            },
        ]);

        let segments = parse_onebot11_segments(&payload);
        let round_trip = Value::Array(
            segments
                .iter()
                .map(|segment| {
                    json!({
                        "type": segment.kind,
                        "data": segment.data,
                    })
                })
                .collect(),
        );

        assert_eq!(
            round_trip,
            json!([
                {
                    "type": "custom",
                    "data": {
                        "text": "legacy",
                        "count": "42",
                        "enabled": "true",
                        "missing": "",
                        "nested": "{\"items\":[1,false,null]}",
                    },
                },
            ])
        );
    }

    #[test]
    fn event_ids_are_unique_and_prefixed() {
        let first = next_event_id_inner();
        let second = next_event_id_inner();

        assert!(first.starts_with("evt-"));
        assert!(second.starts_with("evt-"));
        assert_ne!(first, second);
    }
}
