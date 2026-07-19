from collections.abc import Iterator, MutableMapping
from typing import Any


class AttributeKey[T]:
    """Keys to add custom attributes to models."""

    def __init__(self, type_: type[T]) -> None:
        pass


class AttributeMapping(MutableMapping[AttributeKey[Any], Any]):  # type: ignore[explicit-any]
    """Implements a type safe mapping interface using `AttributeKey` as keys."""

    def __init__(self) -> None:
        self._attributes: dict[AttributeKey[Any], Any] = {}  # type: ignore[explicit-any]

    def __getitem__[T](self, key: AttributeKey[T]) -> T:
        return self._attributes[key]  # type: ignore[no-any-return]

    def __setitem__[T](self, key: AttributeKey[T], value: T) -> None:
        self._attributes[key] = value

    def __delitem__[T](self, key: AttributeKey[T]) -> None:
        del self._attributes[key]

    def __iter__(self) -> Iterator[AttributeKey[Any]]:  # type: ignore[explicit-any]
        return iter(self._attributes)

    def __len__(self) -> int:
        return len(self._attributes)
