"""Task dependency graph: deterministic topological order, cycle detection and transitive closure."""
import heapq

from . import native


class GraphError(Exception):
    pass


class CycleError(GraphError):
    def __init__(self, members):
        self.members = sorted(members)
        super().__init__("dependency cycle among: " + ", ".join(self.members))


class TaskGraph:
    """Tasks are identified by code. `depends_on` edges point from a task to its prerequisites."""

    def __init__(self):
        self._duration = {}
        self._deps = {}

    def add_task(self, code, duration):
        if duration < 1:
            raise GraphError(f"{code}: duration must be at least one working day")
        if code in self._duration:
            raise GraphError(f"{code}: duplicate task")
        self._duration[code] = duration
        self._deps[code] = set()

    def add_dependency(self, code, depends_on):
        for name in (code, depends_on):
            if name not in self._duration:
                raise GraphError(f"{name}: unknown task")
        if code == depends_on:
            raise GraphError(f"{code}: a task cannot depend on itself")
        self._deps[code].add(depends_on)

    def tasks(self):
        return sorted(self._duration)

    def duration(self, code):
        return self._duration[code]

    def dependencies(self, code):
        return sorted(self._deps[code])

    def dependents(self, code):
        return sorted(t for t, deps in self._deps.items() if code in deps)

    def edge_count(self):
        return sum(len(deps) for deps in self._deps.values())

    def would_cycle(self, code, depends_on):
        """True when adding the edge would close a loop (depends_on already reaches code)."""
        if code == depends_on:
            return True
        seen, stack = set(), [depends_on]
        while stack:
            cur = stack.pop()
            if cur == code:
                return True
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self._deps.get(cur, ()))
        return False

    def order(self):
        """Topological order; ties are broken by task code so the result is stable."""
        pending = {t: len(deps) for t, deps in self._deps.items()}
        heap = [t for t, n in pending.items() if n == 0]
        heapq.heapify(heap)
        out = []
        while heap:
            cur = heapq.heappop(heap)
            out.append(cur)
            for nxt in self.dependents(cur):
                pending[nxt] -= 1
                if pending[nxt] == 0:
                    heapq.heappush(heap, nxt)
        if len(out) != len(self._duration):
            raise CycleError(t for t, n in pending.items() if n > 0)
        return out

    def layers(self):
        """Group tasks by the longest chain of prerequisites above them (layer 0 has none)."""
        level = {}
        for code in self.order():
            level[code] = 1 + max((level[d] for d in self._deps[code]), default=-1)
        out = {}
        for code, lvl in level.items():
            out.setdefault(lvl, []).append(code)
        return [sorted(out[k]) for k in sorted(out)]

    def transitive(self):
        """Map every task to the sorted list of all tasks it depends on, directly or not (C bitset closure)."""
        codes = self.tasks()
        if len(codes) > native.MAX_TASKS:
            raise GraphError(f"at most {native.MAX_TASKS} tasks per graph")
        index = {c: i for i, c in enumerate(codes)}
        edges = [(index[c], index[d]) for c in codes for d in self._deps[c]]
        try:
            closed = native.closure(len(codes), edges)
        except native.NativeError as exc:
            if exc.code == native.ERR_CYCLE:
                raise CycleError(c for c in codes if self._reaches_self(c)) from exc
            raise
        return {c: [codes[j] for j in closed[i]] for c, i in index.items()}

    def _reaches_self(self, code):
        seen, stack = set(), list(self._deps[code])
        while stack:
            cur = stack.pop()
            if cur == code:
                return True
            if cur not in seen:
                seen.add(cur)
                stack.extend(self._deps[cur])
        return False

    def ready(self, done):
        """Tasks that are not done and whose prerequisites are all done."""
        done = set(done)
        return [t for t in self.tasks() if t not in done and self._deps[t] <= done]
