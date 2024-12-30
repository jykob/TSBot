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

    def format_signature(self, **kwargs: Any) -> str:
        """
        Remove the self argument from the signature.

        `sphinx_autodoc_typehints` only removes the first argument (self) from the signature
        if the `objtype == "method"`.
        """

        signature = super().format_signature(**kwargs)
        return signature.replace("self, ", "")


def setup(app: Sphinx):
    app.add_autodocumenter(DecoratorFactoryMethodDocumenter)

    return {"version": sphinx.__display_version__, "parallel_read_safe": True}
