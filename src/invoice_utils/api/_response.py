from typing import Generic, TypeVar

from pydantic import BaseModel

from invoice_utils.dal import Template

T = TypeVar("T")


class ListResponse(BaseModel, Generic[T]):
    count: int
    items: list[T]


class TemplateResponse(BaseModel):
    name: str
    rules: list[dict]

    @classmethod
    def from_model(cls, model: Template) -> "TemplateResponse":
        return TemplateResponse(name=model.name, rules=model.rules)
