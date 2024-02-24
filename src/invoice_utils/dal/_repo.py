from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar


T = TypeVar("T")


class Repository(Generic[T], metaclass=ABCMeta):
    @abstractmethod
    def list(self) -> list[T]:
        return []

    @abstractmethod
    def create(self, model: T) -> T:
        return model


class MemoryRepository(Repository[T]):
    def list(self) -> list[T]:
        return []

    def create(self, model: T) -> T:
        return model
