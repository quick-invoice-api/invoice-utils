from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ListResponse(Generic[T], BaseModel):
    count: int
    items: list[T]
