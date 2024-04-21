# Commands

Command handlers are a way for the clients to interact with your bot.  
The bot listens to all the channels available to it.

```{note}
Since **_TeamSpeak Query Clients_** act like normal clients, they can only get channel messages inside the channel they are in.
If you want clients to be able to interact with your bot while in other channels, you need to provide them a method
either by allowing them to type in **Server Chat** or by **Direct Message**
```

All commands start with invoker (defaults to `!`) and proceeded by the command name.  
When sending messages to the bot (**Direct Message**), invoker is not needed.  
You can configure invoker symbol when defining [TSBot](tsbot.bot.TSBot) instance.

---

The text after the command is parsed by the bot and passed in as the arguments to the command handler function.

```python
@bot.command("test")
async def test_command(bot: TSBot, ctx: TSCtx, arg1: str, arg2: str): ...
```

---

If a command is defined with `raw=True`, the message **skips parsing**
and the rest of the message is passed in as one argument.

```python
@bot.command("test", raw=True)
async def test_command(bot: TSBot, ctx: TSCtx, arg1: str): ...
```

## Parsing messages

The message is parsed bit by bit, whitespace as a delimiter.

If a value starts with `-`, it is interpreted as the name of the argument
and the following value is bound to that argument name.

If a value starts with a quote (`"` or `'`), the argument is passed as the whole quoted string.
This allows the arguments to have whitespace (_spaces_, _tabs_ and _new lines_).  
The ending quote must match to the one starting the quote and it must have  
a **whitespace behind it** or be the **last character** to be considered as quoted value.
Otherwise the argument will be interpreted as a normal value, quote included.

Parsed output comes in a form of [tuple](tuple)[[str](str), ...]
and [dict](dict)[[str](str), [str](str)].
This output is bound to the command handler as its **_args_** and **_kwargs_** and executed.

### Examples

| Message                                    | Outcome                                                    |
| ------------------------------------------ | ---------------------------------------------------------- |
| `!test arg1 arg2 arg3`                     | `args, kwargs = ('arg1', 'arg2', 'arg3'), {}`              |
| `!test arg1 -arg3 arg3_value arg2 `        | `args, kwargs = ('arg1', 'arg2'), {'arg3': 'arg3_value'}`  |
| `!test "this is a string with whitespace"` | `args, kwargs = ('this is a string with whitespace',), {}` |
| `!test -arg1 "Text 'quotes' in it"`        | `args, kwargs = (), {'arg1': "Text 'quotes' in it"}`       |

## Command syntax

Command parameters are derived from the function definition.  
First two parameters are skipped, since those are reserved for the `bot` and `ctx` parameters.

```python
@bot.command("test", help_text="Test argument parsing")
async def test(
    bot: TSBot,
    ctx: TSCtx,
    arg1: str,
    /,
    arg2: str,
    arg3: str = "default",
    *,
    kw1: str,
    kw2: str = "default_kw",
):
    await bot.respond(ctx, ", ".join((arg1, arg2, arg3, kw1, kw2)))
```

| Arg  | Explanation                                                                               |
| ---- | ----------------------------------------------------------------------------------------- |
| arg1 | Positional only argument. This argument has to be specified and cannot be passed by name. |
| arg2 | Argument that has to be specified either by position or name.                             |
| arg3 | Same as `arg2` but has a default value.                                                   |
| kw1  | Keyword-only argument. This argument must be provided and has to be passed by name.       |
| kw2  | Same as `kw1`, but has default value.                                                     |

Arguments are passed as a [str](str) to the corresponding parameter.  
You need to do further parsing manually if other types are needed.

## Checks

You can define checks to commands.  
Each check is ran concurrently and once all of them have returned,
the main command is executed.

You can attach checks to a command when defining the command:

```python
ALLOWED_UIDS = ("v8t+Jw6+qNDl1KHuDfS7zVjKSws=", "v4Ea8iM9AAWko2K5ysuET4f+4Lk=")


async def check_user(bot: TSBot, ctx: TSCtx, *args: str, **kwargs: str):
    if ctx["invokeruid"] not in ALLOWED_UIDS:
        raise TSPermissionError("User not allowed to run this command")


@bot.command("dangerous", checks=[check_user])
async def dangerous_command(bot: TSBot, ctx: TSCtx):
    print("Running dangerous command")
    # ...
```

If one of the checks fails (raises an exception),  
All of the other checks are cancelled and the main command is **not** executed.
The first exception is re-raised and handled by the [event system](./events.md#built-in-events).  
You should mainly raise exceptions that are based on [TSException](tsbot.exceptions.TSException):

| Exception                                                           | Caused by                                                       |
| ------------------------------------------------------------------- | --------------------------------------------------------------- |
| [TSCommandError](tsbot.exceptions.TSCommandError)                   | Generic command exception                                       |
| [TSPermissionError](tsbot.exceptions.TSPermissionError)             | Client doesn't have the proper permissions to run this command |
| [TSInvalidParameterError](tsbot.exceptions.TSInvalidParameterError) | Client is calling the command improperly                        |

Each check is passed the same arguments as it were a command.  
if you want the check to be more generic, its signature should mainly be:

```python
async def check(bot: TSBot, ctx: TSCtx, *args: str, **kwargs: str):
```
