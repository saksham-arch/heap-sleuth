from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Allocation:
    filename: str
    lineno: int
    size_bytes: int
    count: int

    def __post_init__(self) -> None:
        if not self.filename:
            raise ValueError("filename must not be empty")
        if self.lineno < 1 or self.size_bytes < 0 or self.count < 0:
            raise ValueError("line must be positive and measurements non-negative")


@dataclass(frozen=True)
class AllocationDelta:
    filename: str
    lineno: int
    size_delta_bytes: int
    count_delta: int


def _index(snapshot: Iterable[Allocation]) -> dict[tuple[str, int], Allocation]:
    indexed: dict[tuple[str, int], Allocation] = {}
    for allocation in snapshot:
        key = (allocation.filename, allocation.lineno)
        previous = indexed.get(key)
        if previous is None:
            indexed[key] = allocation
        else:
            indexed[key] = Allocation(
                allocation.filename,
                allocation.lineno,
                previous.size_bytes + allocation.size_bytes,
                previous.count + allocation.count,
            )
    return indexed


def compare_snapshots(
    before: Iterable[Allocation], after: Iterable[Allocation]
) -> list[AllocationDelta]:
    before_index = _index(before)
    after_index = _index(after)
    keys = before_index.keys() | after_index.keys()
    deltas: list[AllocationDelta] = []
    for filename, lineno in keys:
        old = before_index.get((filename, lineno))
        new = after_index.get((filename, lineno))
        size_delta = (new.size_bytes if new else 0) - (old.size_bytes if old else 0)
        count_delta = (new.count if new else 0) - (old.count if old else 0)
        if size_delta or count_delta:
            deltas.append(AllocationDelta(filename, lineno, size_delta, count_delta))
    return sorted(deltas, key=lambda item: (-abs(item.size_delta_bytes), item.filename, item.lineno))

