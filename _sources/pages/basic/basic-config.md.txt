# Basic Configuration

## Configuration File

All configurations for iamai are stored in `config.toml` file. 

The `config.toml` file is a standard [TOML](https://toml.io/) v1.0.0 file. TOML is a 'minimal' configuration file format that easy to read due to obvious semantics. It is recommended to have a basic understanding of the TOML language before proceeding.

iamai configurations are stored in different tables within the config.toml file. iamai's own configurations are in the `bot` table, while all `adapter` and `plugin` configurations are stored in the `adapter` and `plugin` tables, respectively.

iamai iteself has the following configurations:

- **plugins**
  The list of plugins to be loaded , which will be loaded using the `Bot` class's `load_plugins()` method.

- **plugin_dirs**
  The list of plugin directories to be loaded , which will be loaded using the `Bot` classes `load_plugins_from_dirs()` method.

- **adapters**
  The list of adapters to be loaded, which will be loaded sequentially using the `Bot` classes `load_adapters()` method.

Logging-related configurations are found in the `bot.log` table, as follows:

- **level**
  The log level.

- **verbose_exception**
  Detailed exception logging. When set to True, it will add the exception's Traceback。to the log.

Configurations for different adapters or plugins will be placed in sub-tables under `adapter` and `plugin`.

For example, a configuration file with the `cqhttp` adapter configuration looks like this: 

```toml 

[bot]
# iamai's own configurations
plugins = []
plugin_dirs = ["plugins"]
adapters = ["iamai.adapter.cqhttp"]

[bot.log]
# Logging-related configurations
level = "INFO"
verbose_exception = true

[adapter.cqhttp]
# Configuration for the CQHTTP adapter
adapter_type = "reverse-ws"
host = "127.0.0.1"
port = 8080
url = "/cqhttp/ws"
```

You can include any custom, undefined configuration options, and they will be loaded by iamai. These custom configurations can be used in plugins. For example, you can define `superuser` to represent a special user controlling the current machine, or use `nickname` to represent the nickname of the current bot.

```toml

# Custom, unused keys
superuser = 10001
nickname = "Little AI"

[bot]
# iamai's own configurations
plugins = []
plugin_dirs = ["plugins"]
adapters = ["iamai.adapter.cqhttp"]

```

In a plugin, you can access the entire configuration using `self.bot.config`.For example: 

```python

from iamai import Plugin


class Halloiamai(Plugin):
    async def handle(self) -> None:
        await self.event.reply(f"Hello, I am {self.bot.config.nickname}!")

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message":
            return False
        return (
            self.event.user_id == self.bot.config.superuser
            and str(self.event.message).lower() == "hello"
        )
```

### Custom Configuration File or No Configuration File 

You can provide a custom configuration file or use no configuration file by passing the config_file or config_dict attributes when instantiating the Bot object.

iamai will check the file extension of config_file, allowing either .toml or .json files. If the configuration file is a JSON file, it should be a standard JSON file encoded in UTF-8, with content equivalent to the TOML format configuration file.

When specifying the config_dict attribute, iamai will no longer read from the configuration file and will directly read from the given configuration dictionary.

```python

# Custom configuration file name
bot = Bot(config_file="my_config.json")

# No configuration file
bot = Bot(
    config_dict={
        "bot": {
            "plugin_dirs": ["plugins"],
            "adapters": ["iamai.adapter.cqhttp"],
        }
    }
)
```