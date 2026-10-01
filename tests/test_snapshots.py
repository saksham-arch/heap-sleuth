import unittest

from heap_sleuth import (
    Allocation,
    compare_snapshots,
    filter_deltas,
    group_deltas_by_file,
    summarize_deltas,
)


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

    def test_groups_site_deltas_by_file(self) -> None:
        before = [Allocation("a.py", 1, 10, 1), Allocation("a.py", 2, 30, 3)]
        after = [Allocation("a.py", 1, 20, 2), Allocation("a.py", 2, 10, 1)]
        grouped = group_deltas_by_file(compare_snapshots(before, after))
        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0].changed_sites, 2)
        self.assertEqual(grouped[0].size_growth_sites, 1)
        self.assertEqual(grouped[0].size_release_sites, 1)
        self.assertEqual(grouped[0].bytes_grown, 10)
        self.assertEqual(grouped[0].bytes_released, 20)
        self.assertEqual(grouped[0].size_delta_bytes, -10)
        self.assertEqual(grouped[0].count_delta, -1)

    def test_file_ranking_uses_gross_churn_instead_of_net_change(self) -> None:
        deltas = compare_snapshots(
            [
                Allocation("churn.py", 1, 100, 1),
                Allocation("churn.py", 2, 10, 1),
            ],
            [
                Allocation("churn.py", 1, 10, 1),
                Allocation("churn.py", 2, 100, 1),
                Allocation("net.py", 1, 20, 1),
            ],
        )

        churn, net = group_deltas_by_file(deltas)

        self.assertEqual(churn.filename, "churn.py")
        self.assertEqual(churn.bytes_grown, 90)
        self.assertEqual(churn.bytes_released, 90)
        self.assertEqual(churn.size_delta_bytes, 0)
        self.assertEqual(net.filename, "net.py")

    def test_filters_small_allocation_noise(self) -> None:
        deltas = compare_snapshots(
            [],
            [
                Allocation("large.py", 1, 4096, 2),
                Allocation("many.py", 2, 128, 20),
                Allocation("small.py", 3, 64, 1),
            ],
        )
        filtered = filter_deltas(
            deltas, minimum_size_bytes=1024, minimum_count=10
        )
        self.assertEqual({item.filename for item in filtered}, {"large.py", "many.py"})

    def test_validates_delta_thresholds(self) -> None:
        with self.assertRaises(ValueError):
            filter_deltas([], minimum_size_bytes=-1)

    def test_summarizes_growth_release_and_net_change(self) -> None:
        deltas = compare_snapshots(
            [Allocation("old.py", 1, 100, 4), Allocation("mixed.py", 2, 50, 2)],
            [Allocation("new.py", 1, 180, 3), Allocation("mixed.py", 2, 80, 1)],
        )
        summary = summarize_deltas(deltas)
        self.assertEqual(summary.changed_sites, 3)
        self.assertEqual(summary.size_growth_sites, 2)
        self.assertEqual(summary.size_release_sites, 1)
        self.assertEqual(summary.bytes_grown, 210)
        self.assertEqual(summary.bytes_released, 100)
        self.assertEqual(summary.net_size_delta_bytes, 110)
        self.assertEqual(summary.allocations_grown, 3)
        self.assertEqual(summary.allocations_released, 5)
        self.assertEqual(summary.net_count_delta, -2)

    def test_empty_delta_summary_reports_zeroes(self) -> None:
        summary = summarize_deltas([])
        self.assertEqual(summary.changed_sites, 0)
        self.assertEqual(summary.net_size_delta_bytes, 0)


if __name__ == "__main__":
    unittest.main()
