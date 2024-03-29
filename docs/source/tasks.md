# Tasks

Tasks are a great way to schedule coroutines to be run outside your event/command handler.  
Tasks handlers have one argument, the instance of [TSBot](tsbot.bot.TSBot).

```python
async def example_task(bot: TSBot):
    print("Example task called")
    # Do something with the bot


bot.register_task(example_task)
```

if you need more arguments passed, you can use [functools.partial](functools.partial)

```python
async def example_task(bot: TSBot, arg1: int, arg2: str):
    print("Example task called")
    # Do something with the bot


bot.register_task(functools.partial(example_task, arg1=1, arg2="test"))
```

```{warning}
Tasks handling is started before the bot is connected to the server.
If you need the bot to be connected to the TeamSpeak server, Use build-in
`ready` [event](./events.md#built-in-events).
```

## Every task

Every tasks are a way for you to schedule a task to run periodically.
For example you could implement a AFK mover:

```{literalinclude} ../../examples/plugin_AFK_mover.py

```
