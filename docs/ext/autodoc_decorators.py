from __future__ import annotations

from typing import Any

import sphinx
from sphinx.application import Sphinx
from sphinx.ext.autodoc import MethodDocumenter

_DECORATOR_FACTORIES = {
    "TSBot.on",
    "TSBot.once",
    "TSBot.command",
}


class DecoratorFactoryMethodDocumenter(MethodDocumenter):
    """
    Specialized Documenter subclass for decorator factory methods.
    """

    objtype = "decoratorfactorymethod"
    directivetype = "decoratormethod"

    priority = 10  # must be more than MethodDocumenter

    @classmethod
    def can_document_member(cls, member: Any, membername: str, isattr: bool, parent: Any) -> bool:
        return (
            super().can_document_member(member, membername, isattr, parent)
            and member.__qualname__ in _DECORATOR_FACTORIES
        )


def setup(app: Sphinx):
    app.add_autodocumenter(DecoratorFactoryMethodDocumenter)

    return {"version": sphinx.__display_version__, "parallel_read_safe": True}
