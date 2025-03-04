# Api Reference

```{eval-rst}
.. autoclass:: tsbot.bot.TSBot
    :members:
```

---

## Handlers

```{eval-rst}
.. autotype:: tsbot.events.EventHandler

    A handler signature for event handlers.

    .. code:: python

        async def event_handler(bot: TSBot, ctx: TSCtx) -> None: ...

.. autotype:: tsbot.commands.CommandHandler

    A handler signature for command handlers.

    .. code:: python

        async def command_handler(bot: TSBot, ctx: TSCtx, arg1: str, arg2: str) -> None: ...

.. autotype:: tsbot.commands.RawCommandHandler

    A handler signature for raw command handlers.

    .. code:: python

        async def raw_command_handler(bot: TSBot, ctx: TSCtx, msg: str) -> None: ...

.. autotype:: tsbot.tasks.TaskHandler

    A handler signature for task handlers.

    .. code:: python

        async def task_handler(bot: TSBot) -> None: ...

```

---

## Context

```{eval-rst}
.. class:: tsbot.context.TSCtx(ctx)

   Thin wrapper around Pythons dictionary.

   :param collections.abc.Mapping[str, str] ctx:
   :rtype: collections.abc.Mapping[str, str]
```

---

## Query Builder

```{eval-rst}
.. autoclass:: tsbot.query_builder.query

.. autoclass:: tsbot.query_builder.TSQuery
    :members:
```

---

## Responses

```{eval-rst}
.. autoclass:: tsbot.response.TSResponse
    :members:
    :special-members: __getitem__
    :exclude-members: from_server_response
```

---

## Plugins

```{eval-rst}
.. autoclass:: tsbot.plugin.TSPlugin
```

### Handlers

```{eval-rst}
.. autotype:: tsbot.plugin.PluginCommandHandler

    A handler signature for plugin command handlers.

    .. code:: python

        async def plugin_command_handler(self, bot: TSBot, ctx: TSCtx, arg1: str) -> None: ...

.. autotype:: tsbot.plugin.PluginRawCommandHandler

    A handler signature for plugin raw command handlers.

    .. code:: python

        async def plugin_raw_command_handler(self, bot: TSBot, ctx: TSCtx, msg: str) -> None: ...

.. autotype:: tsbot.plugin.PluginEventHandler

    A handler signature for plugin event handlers.

    .. code:: python

        async def plugin_event_handler(self, bot: TSBot, ctx: TSCtx) -> None: ...

```

### Decorators

```{eval-rst}
.. autodecorator:: tsbot.plugin.command

.. autodecorator:: tsbot.plugin.on

.. autodecorator:: tsbot.plugin.once
```

---

## Tasks

```{eval-rst}
.. autoclass:: tsbot.tasks.TSTask
    :members:
```

---

## Exceptions

```{eval-rst}
.. autoexception:: tsbot.exceptions.TSException
    :show-inheritance:

.. autoexception:: tsbot.exceptions.TSResponseError
    :show-inheritance:

.. autoexception:: tsbot.exceptions.TSResponsePermissionError
    :show-inheritance:

.. autoexception:: tsbot.exceptions.TSCommandError
    :show-inheritance:

.. autoexception:: tsbot.exceptions.TSPermissionError
    :show-inheritance:

.. autoexception:: tsbot.exceptions.TSInvalidParameterError
    :show-inheritance:
```
