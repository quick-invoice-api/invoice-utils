from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar


T = TypeVar("T")


class Repository(Generic[T], metaclass=ABCMeta):
    @abstractmethod
    def list(self) -> list[T]:
        pass


class MemoryRepository(Repository[T]):
    def list(self) -> list[T]:
        return []
