# Events

Chapter all about the events and event system.

## Event handlers

You can register event handlers to fire on given event.  
Event is a [str](str) and can be arbitrary.

On given event, all the event handlers registered to that event are called with arguments `handler(bot, event)` where:

- `bot` is an instance of [TSBot](tsbot.bot.TSBot) calling the handler.
- `event` is an instance of [TSEvent](tsbot.events.tsevent.TSEvent) for additional context.

```python
@bot.on("cliententerview")
async def handle_client_enter(bot: TSBot, event: TSEvent):
    print("Client joined the server")
    # ...
```

You can also register `once` handler.  
These handlers are only fired once when the given event happens.

```python
from tsbot import query

@bot.once("ready")
async def move_on_start(bot: TSBot, event: TSEvent):
    # The bot is ready and connected to the server.
    # Move the bot to a different channel.
    bot_info = await bot.send_raw("whoami")

    for channel in await bot.send_raw("channellist"):
        if "Lobby" in channel["channel_name"]:
            move_query = query("clientmove").params(clid=bot_info.first["client_id"], cid=channel["cid"])
            await bot.send(move_query)
            break
```

---

## Built-in events

TSBot has handful of useful built-in events. These are fired when the bot does something internally.

| Event name         | Called when:                                                  |
| ------------------ | ------------------------------------------------------------- |
| `run`              | The bot is starting up.                                       |
| `ready`            | The bot is ready and connected to the server.                 |
| `close`            | The bot is shutting down.                                     |
| `send`             | The bot is sending commands to the server.                    |
| `command_error`    | A command handler raises `TSCommandError` exception.          |
| `permission_error` | A command handler raises `TSPermissionError` exception.       |
| `parameter_error`  | A command handler raises `TSInvalidParameterError` exception. |

---

## Events from the server

TSBot automatically registers itself as a receiver of server notification.  
These notifications are structured as `{notify}{event_name}`.  
`notify` is omitted from the event and the `event_name` is passed as the event into the event system.

---

## Custom events

Since events are arbitrary [str](str), TSBots event system can handle custom events.  
You can emit your own events with [bot.emit()](tsbot.bot.TSBot.emit) method. [bot.emit()](tsbot.bot.TSBot.emit) accepts the event name as its first argument and additional context of [Mapping](typing.Mapping)[[str](str), [str](str)] as the second argument.

This is useful for example passing events from one plugin to another.
