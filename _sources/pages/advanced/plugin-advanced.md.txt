# Advanced Plugin Features 

## Event Propogation Control

Sometimes, we may need to control the propagation of events. Besides the basic `block` attribute, which decides whether the event propagation continues after this plugin execution, iamai provides some methods for advanced logic control.

### `skip()` Method 

The `skip()` method is used to skip the current plugin and continue event propagation. Typically, you could achieve a similar effect using the `return` statement in the `handle()` method. However, the `skip()` method simplifies certain operations in some cases. For example:

```python

from iamai import Plugin


class TestPlugin(Plugin):
    async def handle(self) -> None:
        await self.foo()

    async def rule(self) -> bool:
        return True

    async def foo(self):
        self.skip()


```

The `skip()` method can be called from any method within the plugin class, and it takes immediate effect.

### `stop()` Method

The `stop()` method is used to end the current event propagation. However, please note that when this method is called, the current event propagation is not immediately terminated. Plugins with the same priority as the current one will still be executed. In other words, the `stop()` method prevents plugins with lower priority from being executed.

### `stop()` Method and `block` Attribute 

You may notice that setting the block attribute to `True` and adding a `self.stop()` statement at the end of the `handle()` method do not have much difference. In most cases, they are indeed equivalent, except for one scenario. When an exception occurs in the handle() method, the final self.stop() statement will not be executed, but the block attribute will still take effect. In other words, setting block to True and the following example are roughly equivalent: