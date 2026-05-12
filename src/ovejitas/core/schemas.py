from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict


class StrictModel(BaseModel):
    """Base for request schemas. Forbids unknown fields, strips string whitespace."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _empty_to_none(v: Any) -> Any:
    if isinstance(v, str) and not v.strip():
        return None
    return v


OptionalStr = Annotated[str | None, BeforeValidator(_empty_to_none)]
