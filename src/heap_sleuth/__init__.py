"""Heap snapshot comparison primitives."""

from .snapshots import Allocation, AllocationDelta, compare_snapshots

__all__ = ["Allocation", "AllocationDelta", "compare_snapshots"]

