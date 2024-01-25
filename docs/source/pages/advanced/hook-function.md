# Hook Functions 

iamai provides same hook functions that can be used as decorators. Here's how to use them:

```python
from iamai import Bot

bot = Bot()

@bot.bot_run_hook
async def hook_func(_bot: Bot):
   pass 

if __name__ == "__main__":
   bot.run()
```

::: tip Note
If you are not sure what you are doing, please do not add hook functions.
:::

## Bot-Related Hooks

### Bot Startup 

```python
@bot.bot_run_hook
async def hook_func(_bot: Bot):
   pass 
```

### Bot Exit 

```python
@bot.bot_exit_hook
async def hook_func(_bot: Bot):
   pass
```

::: warning Note
This hook function is not a coroutine!
:::

## Adapter-Related Hooks 

### Adapter Initialization

```python 

@bot.adapter_startup_hook
async def hook_func(_adapter: "T_Adapter"):
  pass 
```

### Adapter Run

```python

@bot.adapter_run_hook
async def hook_func(_adapter: "T_Adapter"):
    pass
```

### Adapter Shutdown 

```python

@bot.adapter_shutdown_hook

async def hook_func(_adapter : "T_Adapter"):
   pass
```

## Event Processing-Related Hooks 

### Event Processing

```python

@bot.event_preprocessor_hook
async def hook_func(_event: "T_Event"):
   pass
```

## Event PostProcessing

```python

@bot.event_postprocessor_hook
async def hook_func(_event: "T_Event"):
   pass 
```