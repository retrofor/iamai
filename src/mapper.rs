use tokio::net::TcpListener;
use tokio::prelude::*;
use tokio_tungstenite::tungstenite::protocol::Message;
use tokio_tungstenite::accept_async;
use pyo3::prelude::*;

#[pyclass]
pub struct WebSocketServer {}

#[pymethods]
impl WebSocketServer {
    #[new]
    pub fn new() -> Self {
        WebSocketServer {}
    }

    pub async fn start(&self, host: String, port: u16) {
        let addr = format!("{}:{}", host, port);
        let listener = TcpListener::bind(&addr).await.unwrap();
        println!("WebSocket server started at ws://{}", addr);

        while let Ok((stream, _)) = listener.accept().await {
            let ws_stream = accept_async(stream).await.unwrap();
            let (mut write, mut read) = ws_stream.split();

            let message = read.next().await.unwrap().unwrap();
            if let Message::Text(text) = message {
                println!("Received message: {}", text);
            }

            write.send(Message::Text("Processed".to_string())).await.unwrap();
        }
    }
}
