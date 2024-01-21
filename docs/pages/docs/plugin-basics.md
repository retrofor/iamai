# Plugin Basics

## Loading Plugins 

In the [Getting Started](./getting-started.md) chapter, we created a `plugins` directory and set it as the plugin directory in the configuration file. Any Python modules placed in the plugins directory (except those starting with _) will be automatically loaded and tested as plugins. Alternatively, you can load plugins "programmatically" without configuring `plugin_dirs` using the following methods.

However, in most cases, you do not need to use the methods below, and it is recommended to load plugins through the configuration options `plugin_dirs` or `plugins`.

## Loading Plugin Directories 

Add the following lines in the `main.py` file:


```python

from iamai import Bot

bot = Bot()
bot.load_plugins_from_dirs(["plugins", "/home/xxx/iamai/plugins"])

if __name__ == "__main__":
    bot.run()

```

This is actually the same as configuring plugin_dirs to ["plugins", "/home/xxx/iamai/plugins"]. The directories can be relative paths or absolute paths. Plugins starting with _ will not be loaded.

## Loading Individual Plugins 

Add the following lines in the `main.py` file: 

```python

from iamai import Bot

class TestPlugin(Plugin):
   pass

bot = Bot()
bot.load_plugins("plugins.hello", TestPlugin)

if __name__ == "__main__":
   bot.run()
```

The `load_plugins` method can take a plugin class, a string, or a `pathlib.Path` object. If it's the latter two, it will be considered as the name of the plugin module (in the same format as Python's `import` statement) and the path of the plugin module file, respectively.

## Writing Plugins

Each plugin is a plugin class.

Although not mandatory, it is recommended to place each plugin class in a separate Python module.

```text
.
├── plugins
│   ├── a.py (single Python file)
│   └── b (Python package)
│      └── __init__.py
├── config.toml
└── main.py

```

Plugin classes must be subclasses of the Plugin class and must implement the `rule()` and `handle()` methods.


```python

from iamai import Plugin


class TestPlugin(Plugin):
    priority: int = 0
    block: bool = False

    async def handle(self) -> None:
        pass

    async def rule(self) -> bool:
        return True

```

While the class name `TestPlugin` is not mandatory, it is recommended to use meaningful names for better readability.

The priority attribute represents the priority of the plugin, where a smaller number indicates a higher priority.

The block attribute determines whether to stop event propagation after the current plugin is executed. If set to `True`, event propagation will stop after the current plugin completes, and plugins with lower priorities will not be executed.

Both priority and block are optional, and their default values are 0 and False, respectively.


As mentioned in the section [How Does it Work?](), when an adapter generates an event (e.g., the robot receives a message), the event will be dispatched to various plugins based on their priorities. iamai will then execute the rule() method of each plugin one by one to determine whether the handle() method should be executed.

The `Plugin` class has built-in attributes and methods:

- `self.event`: The event currently being processed by this plugin.
- `self.name`: The name of the plugin class.
- `self.bot`: The robot object.
- `self.config`: The plugin configuration.
- `self.state`: The plugin state.
- `self.stop()`: Stops the current event propagation.
- `self.skip()`: Skips itself and continues event propagation.
All attributes and methods except for `self.event` will be discussed in detail in the section [Advanced Plugins](./plugin-advanced) .

Different adapters generate different events. In the following example, we will write a "Hello" plugin using the CQHTTP adapter.


## Writing the `rule()` Method 

```python {9-13}

from iamai import Plugin

class Halloiamai(Plugin):
    async def handle(self) -> None:
        pass

    async def rule(self) -> bool:
        return (
            self.event.adapter.name == "cqhttp"
            and self.event.type == "message"
            and str(self.event.message).lower() == "hello"
        )

```

If you find putting all the conditions in one line less readable, you can write it like this:

```python{9-13} 

from iamai import Plugin


class Halloiamai(Plugin):
    async def handle(self) -> None:
        pass

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message":
            return False
        return str(self.event.message).lower() == "hello"

```


As different adapters generate different events, you should first check the name of the adapter that generated the current event.

Then, check the type of the current event. For CQHTTP adapter, the event types are `message`, `notice`, and `request`, where only message type has the `message` attribute. This plugin only responds to message events.

The `message` attribute of CQHTTP adapter message events represents the received message and is of type `CQHTTPMessage`, which is a subclass of the built-in Message class in iamai.

The built-in Message class in iamai implements many useful methods. It is recommended that all adapter developers use it as much as possible. Specific usage is mentioned in the [Advanced Plugins](./plugin-advanced.md) section. Here, you can directly use the `str()` function to convert the Message object `self.event.message` to a string.

In addition, commonly used methods in the `rule()` method are `self.event.message.startswith('xxx')` and `self.event.message.endswith('xxx')`, which are equivalent to the `startswith()` and `endswith()` methods of strings.

## Writing the `handle()` method 

```python

from iamai import Plugin


class Halloiamai(Plugin):
    async def handle(self) -> None:
        await self.event.reply("Hello, iamai!")

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message":
            return False
        return str(self.event.message).lower() == "hello"

```

As mentioned above, when the rule() method returns `True`, the `handle()` method will be called. Here, we used a method of the message event, `reply()`, to quickly reply to the current message without specifying the recipient of the message.

The `reply()` method is an asynchronous method, so you must use `await` when calling it to wait for it to return.

Now let's look at another example to learn more usage.



## Example : Weather Plugin

```python
from iamai import Plugin
from iamai.exceptions import GetEventTimeout


class Weather(Plugin):
    async def handle(self) -> None:
        args = self.event.get_plain_text().split(" ")
        if len(args) >= 2:
            await self.event.reply(await self.get_weather(args[1]))
        else:
            await self.event.reply("Please enter the city you want to query:")
            try:
                city_event = await self.event.adapter.get(
                    lambda x: x.type == "message", timeout=10
                )
            except GetEventTimeout:
                return
            else:
                await self.event.reply(
                    await self.get_weather(city_event.get_plain_text())
                )

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message":
            return False
        return self.event.message.startswith("weather")

    @staticmethod
    async def get_weather(city):
        if city not in ["Beijing", "Shanghai"]:
            return "The city you want to query is not supported yet!"
        return f"The weather in {city} is..."


```

You can send a message to the robot in the format weather Beijing to get the weather information for Beijing. Alternatively, you can just send weather, and the robot will ask you for the city to query, then you can send the name of the city to query the weather.

In this example, the plugin needs to get the next received message. We use the get() method for this, which is used to obtain events that meet certain conditions. It is also an asynchronous method, so use await to wait for it.

Note that the get() method can specify a timeout to avoid waiting for events indefinitely. When a timeout occurs, it will raise the iamai.exception.GetEventTimeout exception. Be sure to handle this situation properly.

Also, the get_weather() method here does not actually fetch real weather data. You can use any weather API, but when making network requests, use asynchronous libraries like aiohttp or httpx, rather than synchronous ones like requests, to avoid blocking the program.

By reading up to this point, you should be able to write an iamai plugin. Next, we suggest you continue reading Advanced Plugins and the tutorial for the adapter you are going to use.




