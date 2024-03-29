from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar, Optional

from pydantic import BaseModel


K = TypeVar("K")
T = TypeVar("T", bound=BaseModel)


class Repository(Generic[K, T], metaclass=ABCMeta):
    @abstractmethod
    def list(self) -> list[T]:
        return []

    @abstractmethod
    def create(self, model: T) -> T:
        return model

    @abstractmethod
    def get_by_key(self, key: K) -> tuple[bool, Optional[T]]:
        pass

    @abstractmethod
    def delete(self, key: K) -> bool:
        pass

    @abstractmethod
    def exists(self, key: K) -> bool:
        pass

    @abstractmethod
    def update(self, key: K, model: T) -> T:
        pass
