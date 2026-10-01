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


@dataclass(frozen=True)
class FileDelta:
    filename: str
    changed_sites: int
    size_growth_sites: int
    size_release_sites: int
    bytes_grown: int
    bytes_released: int
    size_delta_bytes: int
    count_delta: int


@dataclass(frozen=True)
class DeltaSummary:
    changed_sites: int
    size_growth_sites: int
    size_release_sites: int
    bytes_grown: int
    bytes_released: int
    net_size_delta_bytes: int
    allocations_grown: int
    allocations_released: int
    net_count_delta: int


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


def group_deltas_by_file(deltas: Iterable[AllocationDelta]) -> list[FileDelta]:
    grouped: dict[str, list[AllocationDelta]] = {}
    for delta in deltas:
        grouped.setdefault(delta.filename, []).append(delta)
    results = [
        FileDelta(
            filename=filename,
            changed_sites=len(items),
            size_growth_sites=sum(item.size_delta_bytes > 0 for item in items),
            size_release_sites=sum(item.size_delta_bytes < 0 for item in items),
            bytes_grown=sum(max(item.size_delta_bytes, 0) for item in items),
            bytes_released=sum(max(-item.size_delta_bytes, 0) for item in items),
            size_delta_bytes=sum(item.size_delta_bytes for item in items),
            count_delta=sum(item.count_delta for item in items),
        )
        for filename, items in grouped.items()
    ]
    return sorted(
        results,
        key=lambda item: (-(item.bytes_grown + item.bytes_released), item.filename),
    )


def filter_deltas(
    deltas: Iterable[AllocationDelta],
    *,
    minimum_size_bytes: int = 0,
    minimum_count: int = 0,
) -> list[AllocationDelta]:
    """Keep changes meeting either caller-selected absolute threshold."""
    if minimum_size_bytes < 0 or minimum_count < 0:
        raise ValueError("delta thresholds must be non-negative")
    items = list(deltas)
    if minimum_size_bytes == 0 and minimum_count == 0:
        return items
    return [
        item
        for item in items
        if (
            minimum_size_bytes > 0
            and abs(item.size_delta_bytes) >= minimum_size_bytes
        )
        or (minimum_count > 0 and abs(item.count_delta) >= minimum_count)
    ]


def summarize_deltas(deltas: Iterable[AllocationDelta]) -> DeltaSummary:
    items = list(deltas)
    return DeltaSummary(
        changed_sites=len(items),
        size_growth_sites=sum(item.size_delta_bytes > 0 for item in items),
        size_release_sites=sum(item.size_delta_bytes < 0 for item in items),
        bytes_grown=sum(max(item.size_delta_bytes, 0) for item in items),
        bytes_released=sum(max(-item.size_delta_bytes, 0) for item in items),
        net_size_delta_bytes=sum(item.size_delta_bytes for item in items),
        allocations_grown=sum(max(item.count_delta, 0) for item in items),
        allocations_released=sum(max(-item.count_delta, 0) for item in items),
        net_count_delta=sum(item.count_delta for item in items),
    )
