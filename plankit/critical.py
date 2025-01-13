"""Critical path method over working-day offsets: earliest/latest times, slack and the critical chain."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Timing:
    code: str
    duration: int
    es: int
    ef: int
    ls: int
    lf: int

    @property
    def slack(self):
        return self.ls - self.es

    @property
    def critical(self):
        return self.slack == 0


def analyse(graph, floors=None):
    """Forward and backward pass. `floors` maps a task code to the earliest offset it may start at."""
    floors = floors or {}
    order = graph.order()
    es, ef = {}, {}
    for code in order:
        start = max([floors.get(code, 0)] + [ef[d] for d in graph.dependencies(code)])
        es[code] = start
        ef[code] = start + graph.duration(code)
    length = max(ef.values(), default=0)
    ls, lf = {}, {}
    for code in reversed(order):
        late_finish = min([ls[n] for n in graph.dependents(code)] + [length])
        lf[code] = late_finish
        ls[code] = late_finish - graph.duration(code)
    return {c: Timing(c, graph.duration(c), es[c], ef[c], ls[c], lf[c]) for c in order}


def project_length(timings):
    return max((t.ef for t in timings.values()), default=0)


def critical_path(graph, timings):
    """One longest chain of zero-slack tasks from first start to last finish, in execution order."""
    length = project_length(timings)
    ends = sorted(c for c, t in timings.items() if t.critical and t.ef == length)
    if not ends:
        return []
    chain = [ends[0]]
    while True:
        cur = timings[chain[-1]]
        prev = [d for d in graph.dependencies(cur.code) if timings[d].critical and timings[d].ef == cur.es]
        if not prev:
            break
        chain.append(sorted(prev)[0])
    chain.reverse()
    return chain


def near_critical(timings, threshold):
    """Tasks that are not critical but have at most `threshold` working days of slack."""
    return sorted(c for c, t in timings.items() if 0 < t.slack <= threshold)
