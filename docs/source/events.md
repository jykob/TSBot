# Events

Chapter all about the events and event system.

## Event handlers

You can register event handlers to fire on given event.

On given event, all the event handlers registered to that event name are called with arguments `handler(bot, ctx)` where:

| Arg   | Explanation                                               |
| ----- | --------------------------------------------------------- |
| `bot` | Instance of [TSBot](tsbot.bot.TSBot) calling the handler. |
| `ctx` | Additional context of the event                           |

```python
@bot.on("cliententerview")
async def handle_client_enter(bot: TSBot, ctx: TSCtx):
    print("Client joined the server")
    # ...
```

You can also register `once` handler.  
These handlers are only fired once when the given event happens.

```python
from tsbot import query

@bot.once("ready")
async def move_on_start(bot: TSBot, ctx: None):
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

| Event name         | Called when:                                        | Context type   |
| ------------------ | --------------------------------------------------- | -------------- |
| `run`              | The bot is starting up.                             | [None](None)   |
| `connect`          | The bot has connected to the server.                | [None](None)   |
| `disconnect`       | The bot has lost the connection to the server.      | [None](None)   |
| `reconnect`        | The bot has regained a connection to the server     | [None](None)   |
| `close`            | The bot is shutting down.                           | [None](None)   |
| `send`             | The bot is sending a query to the server.           | [TSCtx](TSCtx) |
| `command_error`    | Handler raises `TSCommandError` exception.          | [TSCtx](TSCtx) |
| `permission_error` | Handler raises `TSPermissionError` exception.       | [TSCtx](TSCtx) |
| `parameter_error`  | Handler raises `TSInvalidParameterError` exception. | [TSCtx](TSCtx) |

---

## Events from the server

TSBot automatically registers itself as a receiver of server notification.  
These notifications are structured as `{notify}{event}`.  
`notify` is omitted from the event and the `event` is passed as the event into the event system.

---

## Custom events

Since event names are arbitrary [str](str), the event system can handle custom events.  
You can emit your own events with [bot.emit()](tsbot.bot.TSBot.emit) method.  
[bot.emit()](tsbot.bot.TSBot.emit) accepts the event name as its first argument and arbitrary context type as the second argument.

This can be useful when passing events from one plugin to another.

```python
score: defaultdict[str, int] = defaultdict(int)


@bot.on("increment_score")
async def increment_user_score(bot: TSBot, uid: str):
    score[uid] += 1


@bot.on("cliententerview")
async def handle_client_enter(bot: TSBot, ctx: TSCtx):
    bot.emit("increment_score", ctx["client_unique_identifier"])
```
