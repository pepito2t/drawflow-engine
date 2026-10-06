from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo

from engine.core.messages import t

FORM_LABEL = t("validation.form_label")


def describe_validation_error(model: type[BaseModel], error: ValidationError) -> str:
    """Lists invalid fields by their user-facing label rather than their technical name."""
    return "; ".join(
        f"{_field_label(model, issue['loc'])} ({issue['msg']})" for issue in error.errors()
    )


def _field_label(model: type[BaseModel], location: tuple[int | str, ...]) -> str:
    if not location:
        return FORM_LABEL
    field: FieldInfo | None = model.model_fields.get(str(location[0]))
    if field is None or field.title is None:
        return ".".join(str(part) for part in location)
    return field.title
