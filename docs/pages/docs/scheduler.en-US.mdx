# Scheduled Tasks

iamai's scheduled tasks are implemented using the [APScheduler](https://apscheduler.readthedocs.io/) library. iamai wraps it into an adapter, providing the same interface as other regular adapters.

## Downloading and Loading the Adapter 

Like other adapters, the scheduled task adapter also needs to be downloaded separately:

```sh
pip install iamai-adapter-apscheduler
```

Alternatively, you can install it along with iamai:

```sh 

pip install iamai[apscheduler]

```

Once downloaded, you can configure it in the `config.toml` file just like any other adapter:


```toml

[bot]
adapters = ["iamai.adapter.xxxx", "iamai.adapter.apscheduler"]

```

Or you can manually load it:

```python

from iamai import Bot

bot = Bot()
bot.load_adapters("iamai.adapter.apscheduler")

if __name__ == "__main__":
    bot.run()

```

However, please note that when manually loading the adapter, you need to load the adapter after loading all the plugins.

## Configuring APScheduler

The `iamai-adapter-apscheduler` adapter has only one configuration item, `scheduler_config`:

```toml

[bot]
adapters = ["iamai.adapter.xxxx", "iamai.adapter.apscheduler"]

[adapter.apscheduler]
scheduler_config = { "apscheduler.timezone" = "Asia/Shanghai" }

```

Please refer to the APScheduler documentation for specific configuration options: [scheduler-config](https://apscheduler.readthedocs.io/en/latest/userguide.html#scheduler-config) . 

## Usage 

### Adding Attributes Directly

After loading the adapter, for plugins that need to be executed on a schedule, they should have a format similar to the following:

```python

from iamai import Plugin


class TestPlugin(Plugin):
    __schedule__ = True
    trigger = "interval"
    trigger_args = {"seconds": 10}

    async def handle(self) -> None:
        pass

    async def rule(self) -> bool:
        return (
            self.event.adapter.name == "apscheduler"
            and type(self) == self.event.plugin_class
        )

```

Scheduled plugins must have the `__schedule__`, `trigger`, and `trigger_args` attributes set.

`__schedule__` must be set to True.
`trigger` represents the APScheduler trigger.
`trigger_args` represents the adapter configuration. They will be passed to the `add_job()` method of the scheduler in the following form:

```python

scheduler.add_job(func, trigger, **trigger_args)

```

The APScheduler adapter will iterate over all plugins during startup, looking for plugins that meet the above criteria, and add scheduled tasks based on the plugin descriptions.

When a scheduled task is triggered, the APScheduler adapter will generate an event and perform normal event propagation.

This event's `type` attribute is always apscheduler, and it has a `plugin_class` attribute representing the plugin class that defined this scheduled task. You can use `type(self) == self.event.plugin_class` in the `rule()` method to ensure that this plugin only handles its own defined scheduled events.


##  Using Class Decorators (Recommended)


In addition to the above method, you can also use class decorators to decorate an existing plugin as a scheduled task plugin.

```python

from iamai import Plugin
from iamai.adapter.apscheduler import scheduler_decorator


@scheduler_decorator(
    trigger="interval", trigger_args={"seconds": 10}, override_rule=True
)
class TestPlugin(Plugin):
    async def handle(self) -> None:
        pass

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message":
            return False
        return str(self.event.message).lower() == "hello"

```

The above syntax is equivalent to:

```
from iamai import Plugin


class TestPlugin(Plugin):
    __schedule__ = True
    trigger = "interval"
    trigger_args = {"seconds": 10}

    async def handle(self) -> None:
        pass

    async def rule(self) -> bool:
        if self.event.name == "apscheduler" and type(self) == self.event.plugin_class:
            return True
        else:
            if self.event.adapter.name != "cqhttp":
                return False
            if self.event.type != "message":
                return False
            return str(self.event.message).lower() == "hello"

```

As shown in the above example, setting the `override_rule` parameter to True can automatically override the `rule()` method and add the logic to handle the scheduled task events.

## Tips 

When the same scheduled task needs to wake up multiple plugins simultaneously, and multiple scheduled tasks are set, and you do not want them to interfere with each other, you can do as follows:

First Plugin:

```python

from iamai import Plugin
from iamai.adapter.apscheduler import scheduler_decorator


@scheduler_decorator(
    trigger="interval", trigger_args={"seconds": 10}, override_rule=False
)
class PluginA(Plugin):
    scheduler_flag = "abc"

    async def handle(self) -> None:
        pass

    async def rule(self) -> bool:
        if (
            self.event.type == "apscheduler"
            and getattr(self.event.plugin_class, "scheduler_flag", "") == "abc"
        ):
            return True
        else:
            pass

```

Second Plugin: 

```python

from iamai import Plugin


class PluginB(Plugin):
    async def handle(self) -> None:
        pass

    async def rule(self) -> bool:
        if (
            self.event.type == "apscheduler"
            and getattr(self.event.plugin_class, "scheduler_flag", "") == "abc"
        ):
            return True
        else:
            pass

```
You need to set a unique `scheduler_flag` attribute for the plugin that defines the scheduled task. Of course, this attribute can also be named anything else. Then the second plugin can determine the value of `scheduler_flag` to judge whether the current event is a scheduled event defined by the first plugin.


## Example 

Now let's try using the CQHTTP protocol adapter to send a message on a schedule.

```python

from time import strftime, localtime

from iamai import Plugin
from iamai.adapter.apscheduler import scheduler_decorator


@scheduler_decorator(
    trigger="interval", trigger_args={"seconds": 100}, override_rule=True
)
class Schedule(Plugin):
    async def handle(self) -> None:
        await self.bot.get_adapter("cqhttp").send(
            f"Time: {strftime('%Y-%m-%d %H:%M:%S', localtime())}",
            message_type="group",
            id_=1234567890,  # Group ID
        )

    async def rule(self) -> bool:
        return False


```
