# Api Reference

## Bot

```{eval-rst}
.. autoclass:: tsbot.bot.TSBot
    :members:
    :undoc-members:
    :exclude-members: on, once, command, task, every

    .. autodecorator:: tsbot.bot.TSBot.on()
    .. autodecorator:: tsbot.bot.TSBot.once()
    .. autodecorator:: tsbot.bot.TSBot.command()
    .. autodecorator:: tsbot.bot.TSBot.task()
    .. autodecorator:: tsbot.bot.TSBot.every()
```

## Events

```{eval-rst}
.. autoclass:: tsbot.events.TSEvent
```

## Context

```{eval-rst}
.. class:: tsbot.context.TSCtx(ctx)

    A wrapper around pythons dictionary

   :param typing.Mapping[str, str] ctx:
   :rtype: typing.Mapping[str, str]
```

## Query

```{eval-rst}
.. autofunction:: tsbot.query_builder.query()

.. autoclass:: tsbot.query_builder.TSQuery
    :members:
```

## Responses

```{eval-rst}
.. autoclass:: tsbot.response.TSResponse
    :members:
```

## Plugins

```{eval-rst}
.. autoclass:: tsbot.plugin.TSPlugin
.. autodecorator:: tsbot.plugin.on()
.. autodecorator:: tsbot.plugin.once()
.. autodecorator:: tsbot.plugin.command()
.. autodecorator:: tsbot.plugin.task()
.. autodecorator:: tsbot.plugin.every()
```

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
