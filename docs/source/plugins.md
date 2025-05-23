# Plugins

In order to keep your code properly partitioned, TSBot gives you an option to write plugins.  
Plugins allow you to split up your state and functionality from other code.

```{literalinclude} ../../examples/plugin_example.py
:language: python

```

This example is taken from [examples/plugin_example.py](https://github.com/jykob/TSBot/blob/main/examples/plugin_example.py)

---

## Callbacks

TSBot plugins can define callbacks that are called when the plugin is loaded or unloaded.

You can override the [`TSPlugin.on_load()`](tsbot.plugin.TSPlugin.on_load) and [`TSPlugin.on_unload()`](tsbot.plugin.TSPlugin.on_unload)
methods in your plugin class to do side effects when the plugin is loaded or unloaded.

```{literalinclude} ../../examples/plugin_callbacks.py
:language: python

```

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
When a `help` command is invoked with a `command` as its first argument,
the bot will respond with the given `help_text` (passed as an argument when defining the command)
and the usage of such command.

```{image} ../img/plugins/help-brief.png
:alt: Brief command help text
```

For more detailed output, users can pass in `-detailed` flag (a keyword argument without any values after it)
or by passing `-format detailed` as a keyword argument.

```{image} ../img/plugins/help-detailed.png
:alt: Detailed command help text
```

```{note}
If no command were found or the command is `hidden`, the `help` command raises
[TSCommandError](tsbot.exceptions.TSCommandError) telling that no command was found.
```
