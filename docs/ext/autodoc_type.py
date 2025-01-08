from __future__ import annotations

import typing
from typing import Any, cast

import sphinx
from sphinx.application import Sphinx
from sphinx.ext.autodoc import DataDocumenterMixinBase, ModuleLevelDocumenter
from sphinx.util.typing import stringify_annotation

TypeParams = typing.TypeVarTuple | typing.TypeVar | typing.ParamSpec


def get_obj_type_args(obj: object) -> tuple[TypeParams, ...]:
    if isinstance(obj, TypeParams):
        return (obj,)

    results: list[TypeParams] = []

    for arg in cast(list[Any], obj) if isinstance(obj, list) else typing.get_args(obj):
        results.extend(result for result in get_obj_type_args(arg) if result not in results)

    return tuple(results)


def format_typevar(typevar: typing.TypeVar) -> str:
    formatted = typevar.__name__

    if bound := getattr(typevar, "__bound__", None):
        formatted += f": {stringify_annotation(bound, "smart")}"

    return formatted


def format_paramspec(paramspec: typing.ParamSpec) -> str:
    return f"**{paramspec.__name__}"


def format_typevartuple(typevartuple: typing.TypeVarTuple) -> str:
    return f"*{typevartuple.__name__}"


def format_type_parameters(type_param: TypeParams) -> str:
    match type_param:
        case typing.TypeVar():
            return format_typevar(type_param)
        case typing.ParamSpec():
            return format_paramspec(type_param)
        case typing.TypeVarTuple():
            return format_typevartuple(type_param)


class TypeDocumenter(DataDocumenterMixinBase, ModuleLevelDocumenter):
    objtype = "type"
    directivetype = "type"

    priority = ModuleLevelDocumenter.priority + 10

    @classmethod
    def can_document_member(cls, member: Any, membername: str, isattr: bool, parent: Any) -> bool:
        return False

    def document_members(self, all_members: bool = False) -> None:
        pass

    def format_name(self) -> str:
        ret = super().format_name()

        if type_params := get_obj_type_args(self.object):
            ret += f"[{', '.join(map(format_type_parameters, type_params))}]"

        return ret

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()

        if self.config.autodoc_typehints_format == "short":
            object_repr = stringify_annotation(self.object, "smart")
        else:
            object_repr = stringify_annotation(self.object, "fully-qualified-except-typing")

        self.add_line("   :canonical: " + object_repr, sourcename)


def setup(app: Sphinx):
    app.setup_extension("sphinx.ext.autodoc")
    app.add_autodocumenter(TypeDocumenter)

    return {"version": sphinx.__display_version__, "parallel_read_safe": True}
