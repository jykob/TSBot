# Api Reference

## TSBot

```{eval-rst}

.. autoclass:: tsbot.TSBot
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
