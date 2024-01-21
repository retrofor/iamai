# Hot Reload 

## Manual Cold Reload

iamai provides a `restart()` method to exit and restart the iamai. You can write a plugin like this to restart iamai:

```python

from iamai import Plugin

class Restart(Plugin):
    async def handle(self)-> None:
       self.bot.restart()
    
    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
           return False
        
        if self.event.type != "message":
           return False
        
        return self.event.message.get_plain_text() == "restart"

```

One detail to note is that using this function and manually exiting and restarting iamai have some subtle differences, mainly in that using this function will not clear plugin and global states.

## Reload Plugin

In addition, iamai also provides a `reload_plugins()` method to reload all plugins. This method does not reload configuration files, adapters, etc.

## Automatic Hot Reload

Since version 0.4.0, iamai has supported automatic hot reload. This means that when plugin files or configuration files are updated, iamai does not need to be restarted, and the changes will be automatically loaded.

This feature requires support from the `watchfiles` library, so please manually install this Python library.

When the configuration file is updated, the configuration file will be reloaded. If the bot table changes, the `restart()` method will be called to restart iamai.

When plugin files in the directories set in `plugin_dirs` are added, modified, or deleted, iamai will automatically try to import, reload, or delete the corresponding plugins.

Enabling this feature is very simple, just pass the `hot_reload` parameter when instantiating the `Bot` class.

```python

from iamai import Bot

bot = Bot(hot_reload=True)

if __name__ == "__main__":
   bot.run()
```


However, please note that this feature is still in early experimental stage. If you encounter any issues during use, please provide feedback. Also, this feature may slightly affect performance, so if your use case is highly performance-sensitive, do not enable this feature in production environments.