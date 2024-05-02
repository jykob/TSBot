import inspect
from typing import Any

import sphinx
from sphinx.application import Sphinx
from sphinx.ext.autodoc import MethodDocumenter


class DecoratorMethodDocumenter(MethodDocumenter):
    """
    Specialized Documenter subclass for decorator methods.
    """

    # TODO: Figure out a way to remove `self` from method signature.

    objtype = "decoratormethod"
    directivetype = "decorator"

    priority = 10

    @classmethod
    def can_document_member(cls, member: Any, membername: str, isattr: bool, parent: Any) -> bool:
        return (
            super().can_document_member(member, membername, isattr, parent)
            and bool(docstring := inspect.getdoc(member))
            and docstring.startswith(("decorator", "Decorator"))
        )


def setup(app: Sphinx):
    app.add_autodocumenter(DecoratorMethodDocumenter)

    return {"version": sphinx.__display_version__, "parallel_read_safe": True}
