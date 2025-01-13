import unittest

from plankit.depgraph import CycleError, GraphError, TaskGraph

from .graphs import diamond


class GraphBuildTests(unittest.TestCase):
    def test_rejects_bad_tasks(self):
        g = TaskGraph()
        g.add_task("A", 1)
        with self.assertRaises(GraphError):
            g.add_task("A", 2)
        with self.assertRaises(GraphError):
            g.add_task("B", 0)

    def test_rejects_bad_edges(self):
        g = diamond()
        with self.assertRaises(GraphError):
            g.add_dependency("A", "A")
        with self.assertRaises(GraphError):
            g.add_dependency("A", "Z")

    def test_neighbours_and_counts(self):
        g = diamond()
        self.assertEqual(g.dependencies("D"), ["B", "C"])
        self.assertEqual(g.dependents("A"), ["B", "C"])
        self.assertEqual(g.edge_count(), 4)
        self.assertEqual(g.duration("C"), 4)


class OrderTests(unittest.TestCase):
    def test_topological_order_is_stable(self):
        self.assertEqual(diamond().order(), ["A", "B", "C", "D"])

    def test_order_respects_every_edge(self):
        g = TaskGraph()
        for code in "EDCBA":
            g.add_task(code, 1)
        for task, dep in (("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")):
            g.add_dependency(task, dep)
        order = g.order()
        self.assertEqual(order, ["E", "D", "C", "B", "A"])

    def test_cycle_raises_with_members(self):
        g = TaskGraph()
        for code in "ABCX":
            g.add_task(code, 1)
        g.add_dependency("A", "B")
        g.add_dependency("B", "C")
        g.add_dependency("C", "A")
        g.add_dependency("X", "C")
        with self.assertRaises(CycleError) as ctx:
            g.order()
        self.assertEqual(ctx.exception.members, ["A", "B", "C", "X"])

    def test_layers(self):
        self.assertEqual(diamond().layers(), [["A"], ["B", "C"], ["D"]])

    def test_ready_tasks(self):
        g = diamond()
        self.assertEqual(g.ready([]), ["A"])
        self.assertEqual(g.ready(["A"]), ["B", "C"])
        self.assertEqual(g.ready(["A", "B"]), ["C"])
        self.assertEqual(g.ready(["A", "B", "C"]), ["D"])


class ClosureTests(unittest.TestCase):
    def test_would_cycle(self):
        g = diamond()
        self.assertTrue(g.would_cycle("A", "D"))
        self.assertTrue(g.would_cycle("B", "B"))
        self.assertFalse(g.would_cycle("D", "A"))

    def test_transitive_uses_the_bitset_closure(self):
        self.assertEqual(diamond().transitive(), {"A": [], "B": ["A"], "C": ["A"], "D": ["A", "B", "C"]})

    def test_transitive_cycle(self):
        g = TaskGraph()
        for code in "AB":
            g.add_task(code, 1)
        g.add_dependency("A", "B")
        g.add_dependency("B", "A")
        with self.assertRaises(CycleError) as ctx:
            g.transitive()
        self.assertEqual(ctx.exception.members, ["A", "B"])

    def test_graph_size_limit(self):
        g = TaskGraph()
        for i in range(129):
            g.add_task(f"T{i:03d}", 1)
        with self.assertRaises(GraphError):
            g.transitive()

    def test_large_chain(self):
        g = TaskGraph()
        for i in range(100):
            g.add_task(f"T{i:03d}", 1)
        for i in range(1, 100):
            g.add_dependency(f"T{i:03d}", f"T{i - 1:03d}")
        closed = g.transitive()
        self.assertEqual(len(closed["T099"]), 99)
        self.assertEqual(closed["T000"], [])
