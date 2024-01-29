# Plugins

In this chapter we will walk you through everything there is about the plugin system.

---

## Writing plugins

In order to keep your code properly partitioned, {{env.config.project}} gives you options to write plugins.  
Plugins allow you to split up your functionality from other code.

Let's check out [examples/plugin_example.py](https://github.com/0x4aK/TSBot/blob/master/examples/plugin_example.py) and walk through the code.  
**TLDR**: Complete example down [here](complete-example)

---

First off we import all the modules we need: [asyncio](asyncio) and few modules from tsbot.

```{literalinclude} ../../examples/plugin_example.py
:linenos:
:lines: -5
```

```{note}
importing [TSCtx](tsbot.context.TSCtx) and [TSEvent](tsbot.events.TSEvent) isn't strictly necessary. Here it's only used for typehints.
```

---

```{literalinclude} ../../examples/plugin_example.py
:linenos:
:lineno-start: 8
:lines: 8-11
```

We create a class that inherits from [plugin.TSPlugin](tsbot.plugin.TSPlugin).  
In the `__init__()` method, we define 2 instance variables, `self.message` and `self.move_message`. These will be used later inside the methods.

```{important}
All plugins must inherit from [plugin.TSPlugin](tsbot.plugin.TSPlugin)
```

---

Lets define some `Commands` and `Event handlers`. These are better documented in their own sections, refer to those when needed.  
The only difference is that instead of prefixing decorators with `bot`, plugins use `plugin`.

```{literalinclude} ../../examples/plugin_example.py
:linenos:
:lineno-start: 13
:lines: 13-22
```

Notice how we are using the `self.message` and `self.move_message` from the `__init__()` method.  
Plugins work like normal classes, they have access to their respected class/instance variables.

---

Now lets make a [TSBot](tsbot.bot.TSBot) instance. After that, we use the
[load_plugin()](<tsbot.bot.TSBot.load_plugin()>) method to load an instance of our `TestPlugin`.

```{literalinclude} ../../examples/plugin_example.py
:linenos:
:lineno-start: 25
:lines: 25-
```

Finally we start the bot with [asyncio.run()](asyncio.run).

---

(complete-example)=
The complete example:

```{literalinclude} ../../examples/plugin_example.py
:linenos:
```

The best part is that you don't have to define your plugins in the module. You can create plugins in their own file and import them in the main file.

---

## Default plugins

{{env.config.project}} comes with a few useful default plugins. These include:

### KeepAlive

Since TeamSpeak servers will close your connection to them if you don't send it commands from time to time.
This time is around **_5 minutes_** of inactivity.

KeepAlive plugin hooks into builtin event `send`. If send event hasn't been seen for **_4 minutes_**,
the plugin will send a ping to the server.

### Help

The Help plugin implements `help` command.  
When `help` command is invoked, the bot will respond to the command with the given `help_text` and usage of the command.

```{image} ../img/plugins/help_example.png
:alt: Example of help command
```

```{note}
If the command wasn't found or the command is `hidden`, the `help` command raises
[TSCommandError](tsbot.exceptions.TSCommandError) telling that the command wasn't found.
```
