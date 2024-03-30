# Api Reference

```{eval-rst}
.. autoclass:: tsbot.bot.TSBot
    :members:
```

---

```{eval-rst}
.. class:: TSCtx(ctx)

   Thin wrapper around Pythons dictionary.

   :param collections.abc.Mapping[str, str] ctx:
   :rtype: collections.abc.Mapping[str, str]
```

---

```{eval-rst}
.. automodule:: tsbot.query_builder
    :members:
    :exclude-members: Stringable
```

---

```{eval-rst}
.. autoclass:: tsbot.response.TSResponse
    :members:
    :undoc-members:
    :exclude-members: from_server_response
```

## Plugins

```{eval-rst}
.. automodule:: tsbot.plugin
    :members:
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
