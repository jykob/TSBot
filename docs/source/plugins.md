# Plugins

In order to keep your code properly partitioned, TSBot gives you an option to write plugins.  
Plugins allow you to split up your state and functionality from other code.

```{literalinclude} ../../examples/plugin_example.py

```

This example is taken from [examples/plugin_example.py](https://github.com/0x4aK/TSBot/blob/master/examples/plugin_example.py)

---

## Default plugins

TSBot comes with a few useful default plugins. These include:

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
If no command were found or the command is `hidden`, the `help` command raises
[TSCommandError](tsbot.exceptions.TSCommandError) telling that no command was found.
```
