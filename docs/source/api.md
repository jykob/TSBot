# Api Reference

```{eval-rst}
.. autoclass:: tsbot.bot.TSBot
    :members:
```

---

## Context

```{eval-rst}
.. class:: TSCtx(ctx)

   Thin wrapper around Pythons dictionary.

   :param collections.abc.Mapping[str, str] ctx:
   :rtype: collections.abc.Mapping[str, str]
```

---

## Query Builder

```{eval-rst}
.. autoclass:: tsbot.query_builder.query
```

```{eval-rst}
.. autoclass:: tsbot.query_builder.TSQuery
    :members:
```

---

## Responses

```{eval-rst}
.. autoclass:: tsbot.response.TSResponse
    :members:
    :exclude-members: from_server_response
```

---

## Plugins

```{eval-rst}
.. autoclass:: tsbot.plugin.TSPlugin
```

```{eval-rst}
.. autodecorator:: tsbot.plugin.command
```

```{eval-rst}
.. autodecorator:: tsbot.plugin.on
```

```{eval-rst}
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
