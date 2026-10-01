from typing import Any, Literal

from pydantic import Field
from pydantic_core import PydanticUndefined

UiKind = Literal[
    "file",
    "files",
    "folder",
    "folders",
    "output_folder",
    "template",
    "text",
    "number",
    "bool",
    "enum",
]
UI_KIND_SCHEMA_KEY = "x-ui"


def ui_field(
    kind: UiKind,
    *,
    label: str,
    default: Any = PydanticUndefined,
    description: str | None = None,
    **constraints: Any,
) -> Any:
    """Declares a form field; `kind` drives the widget the UI generates."""
    return Field(
        default,
        title=label,
        description=description,
        json_schema_extra={UI_KIND_SCHEMA_KEY: kind},
        **constraints,
    )
