import unittest

from heap_sleuth import Allocation, compare_snapshots


class SnapshotTests(unittest.TestCase):
    def test_reports_growth_release_and_new_sites(self) -> None:
        before = [Allocation("a.py", 10, 100, 2), Allocation("b.py", 5, 50, 1)]
        after = [Allocation("a.py", 10, 140, 3), Allocation("c.py", 7, 200, 4)]
        deltas = compare_snapshots(before, after)
        self.assertEqual(
            [(item.filename, item.size_delta_bytes) for item in deltas],
            [("c.py", 200), ("b.py", -50), ("a.py", 40)],
        )

    def test_merges_duplicate_sites(self) -> None:
        after = [Allocation("a.py", 1, 10, 1), Allocation("a.py", 1, 20, 2)]
        self.assertEqual(compare_snapshots([], after)[0].size_delta_bytes, 30)

    def test_omits_unchanged_sites(self) -> None:
        snapshot = [Allocation("a.py", 1, 10, 1)]
        self.assertEqual(compare_snapshots(snapshot, snapshot), [])

    def test_validates_allocations(self) -> None:
        with self.assertRaises(ValueError):
            Allocation("", 1, 0, 0)


if __name__ == "__main__":
    unittest.main()
