import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .snapshots import Allocation, compare_snapshots


def load_snapshot(path: Path) -> list[Allocation]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("snapshot root must be a list")
    return [
        Allocation(
            filename=str(item["filename"]),
            lineno=int(item["lineno"]),
            size_bytes=int(item["size_bytes"]),
            count=int(item["count"]),
        )
        for item in payload
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare heap allocation snapshots")
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be positive")
    deltas = compare_snapshots(load_snapshot(args.before), load_snapshot(args.after))
    print(json.dumps([asdict(item) for item in deltas[: args.top]], indent=2))


if __name__ == "__main__":
    main()

