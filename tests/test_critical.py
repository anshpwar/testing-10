import unittest

from plankit import critical

from .graphs import build, diamond, two_tracks


class AnalyseTests(unittest.TestCase):
    def test_forward_and_backward_pass(self):
        t = critical.analyse(diamond())
        self.assertEqual((t["A"].es, t["A"].ef), (0, 3))
        self.assertEqual((t["B"].es, t["B"].ef, t["B"].ls, t["B"].lf), (3, 5, 5, 7))
        self.assertEqual((t["C"].es, t["C"].ef), (3, 7))
        self.assertEqual((t["D"].es, t["D"].ef), (7, 8))

    def test_slack_and_criticality(self):
        t = critical.analyse(diamond())
        self.assertEqual({c: x.slack for c, x in t.items()}, {"A": 0, "B": 2, "C": 0, "D": 0})
        self.assertEqual([c for c, x in t.items() if x.critical], ["A", "C", "D"])

    def test_project_length(self):
        self.assertEqual(critical.project_length(critical.analyse(diamond())), 8)
        self.assertEqual(critical.project_length({}), 0)

    def test_floors_delay_a_task_and_its_successors(self):
        t = critical.analyse(diamond(), {"B": 6})
        self.assertEqual((t["B"].es, t["B"].ef), (6, 8))
        self.assertEqual(t["D"].es, 8)
        self.assertEqual(critical.project_length(t), 9)

    def test_floor_inside_the_slack_changes_nothing(self):
        t = critical.analyse(diamond(), {"B": 4})
        self.assertEqual(critical.project_length(t), 8)
        self.assertEqual(t["B"].slack, 1)

    def test_independent_tracks(self):
        t = critical.analyse(two_tracks())
        self.assertEqual({c: x.slack for c, x in t.items()}, {"P1": 1, "P2": 1, "Q1": 0, "R": 0})


class PathTests(unittest.TestCase):
    def test_critical_path(self):
        g = diamond()
        self.assertEqual(critical.critical_path(g, critical.analyse(g)), ["A", "C", "D"])

    def test_critical_path_of_two_tracks(self):
        g = two_tracks()
        self.assertEqual(critical.critical_path(g, critical.analyse(g)), ["Q1", "R"])

    def test_equal_branches_pick_the_first_code(self):
        g = build({"A": 1, "B": 2, "C": 2, "D": 1}, [("B", "A"), ("C", "A"), ("D", "B"), ("D", "C")])
        self.assertEqual(critical.critical_path(g, critical.analyse(g)), ["A", "B", "D"])

    def test_empty_graph(self):
        g = build({})
        self.assertEqual(critical.critical_path(g, critical.analyse(g)), [])

    def test_near_critical_filters_by_threshold(self):
        t = critical.analyse(two_tracks())
        self.assertEqual(critical.near_critical(t, 0), [])
        self.assertEqual(critical.near_critical(t, 1), ["P1", "P2"])
        self.assertEqual(critical.near_critical(critical.analyse(diamond()), 1), [])
        self.assertEqual(critical.near_critical(critical.analyse(diamond()), 2), ["B"])
