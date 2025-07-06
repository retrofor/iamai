bot:
    name: "MyProductionBot"
    version: "1.1.0"
    debug: false
    api_url: "https://production.api.example.com"

log:
    level: "INFO"
    format: "%(asctime)s - %(levelname)s - %(message)s"
    output_file: "bot.log"

plugin:
    enabled_plugins:
        - "plugin_a"
        - "plugin_b"
    plugin_dir: "custom_plugins"

model:
    model_name: "gpt-4"
    temperature: 0.9
    max_tokens: 4096

middleware:
    enabled_middleware:
        - "middleware_x"
        - "middleware_y"
    middleware_settings:
        middleware_x:
            setting1: "value1"
            setting2: 123
        middleware_y:
            setting3: true
