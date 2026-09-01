# heap-sleuth

Deterministic primitives for comparing heap-allocation snapshots. The first
increment compares JSON snapshots by allocation site and reports byte/count
deltas, making growth and release visible without labeling either as a leak.

Snapshot format:

```json
[{"filename":"worker.py","lineno":42,"size_bytes":4096,"count":8}]
```

```bash
PYTHONPATH=src python3 -m heap_sleuth before.json after.json --top 20
python3 -m unittest discover -s tests
```

A positive delta is retained growth between two observations, not proof of a
memory leak. Reproduce growth across controlled workloads before drawing that
conclusion.

