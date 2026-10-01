from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
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
    "mapping",
]
UI_KIND_SCHEMA_KEY = "x-ui"
UI_KEY_LABEL_SCHEMA_KEY = "x-ui-key-label"
UI_VALUE_LABEL_SCHEMA_KEY = "x-ui-value-label"


class KeyValue(BaseModel):
    """One row of a `mapping` field (e.g. column title → attribute tag)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str = Field(min_length=1)
    value: str = Field(min_length=1)


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


def mapping_field(
    *, label: str, key_label: str, value_label: str, default: list[KeyValue], description: str
) -> Any:
    return Field(
        default=default,
        title=label,
        description=description,
        min_length=1,
        json_schema_extra={
            UI_KIND_SCHEMA_KEY: "mapping",
            UI_KEY_LABEL_SCHEMA_KEY: key_label,
            UI_VALUE_LABEL_SCHEMA_KEY: value_label,
        },
    )
