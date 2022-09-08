# Api Reference

```{attention}
Under construction
```

## TSBot

```{eval-rst}
.. autoclass:: tsbot.bot.TSBot
    :members:
    :exclude-members: on, command

    .. autodecorator:: tsbot.TSBot.on()

    .. autodecorator:: tsbot.TSBot.command()
```

## TSClientInfo

```{eval-rst}
.. autoclass:: tsbot.client_info.TSClientInfo
```

## TSEvent

```{eval-rst}
.. autoclass:: tsbot.events.TSEvent
```

## TSQuery

```{eval-rst}
.. autofunction:: tsbot.query_builder.query()

.. autoclass:: tsbot.query_builder.TSQuery
    :members:

```

## TSResponse

```{eval-rst}
.. autoclass:: tsbot.response.TSResponse
    :members:
```

## Plugins

```{eval-rst}
.. autoclass:: tsbot.plugin.TSPlugin

.. autofunction:: tsbot.plugin.command()
.. autofunction:: tsbot.plugin.on()
```

## Exceptions

```{eval-rst}
.. autoexception:: tsbot.exceptions.TSException
    :show-inheritance:
.. autoexception:: tsbot.exceptions.TSResponseError
    :show-inheritance:
.. autoexception:: tsbot.exceptions.TSCommandError
    :show-inheritance:
.. autoexception:: tsbot.exceptions.TSPermissionError
    :show-inheritance:
```
