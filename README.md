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
PYTHONPATH=src python3 -m heap_sleuth before.json after.json --group-by file
PYTHONPATH=src python3 -m heap_sleuth before.json after.json --minimum-size-bytes 4096
PYTHONPATH=src python3 -m heap_sleuth before.json after.json --summary
python3 -m unittest discover -s tests
```

A positive delta is retained growth between two observations, not proof of a
memory leak. Reproduce growth across controlled workloads before drawing that
conclusion.

Site-level output can be grouped by filename to reveal modules with distributed
growth while preserving the number of changed allocation sites.

Optional absolute byte and allocation-count thresholds suppress small deltas;
when both are supplied, a site is retained if it meets either threshold. These
are practical noise filters, not statistical tests or leak classifications.

Summary mode separates bytes and allocation counts that grew from those that
were released, then reports their net changes. The summary is computed after
optional thresholds are applied, while `--top` limits only the displayed delta
rows. Growth remains an observation between snapshots, not proof of a leak.
