from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar


K = TypeVar("K")
T = TypeVar("T")


class Repository(Generic[K, T], metaclass=ABCMeta):
    @abstractmethod
    def list(self) -> list[T]:
        return []

    @abstractmethod
    def create(self, model: T) -> T:
        return model

    @abstractmethod
    def get_by_key(self, key: K) -> T:
        pass


class NotSupportedRepository(Repository[K, T]):
    def list(self) -> list[T]:
        raise NotImplemented()

    def create(self, model: T) -> T:
        raise NotImplemented()

    def get_by_key(self, key: K) -> T:
        raise NotImplemented()