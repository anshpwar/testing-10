"""Effort estimates: three-point averages and confidence-based ranges."""
from . import rules


def three_point(optimistic, likely, pessimistic):
    """PERT estimate in whole working days, rounded half up."""
    if not 0 < optimistic <= likely <= pessimistic:
        raise ValueError("expected 0 < optimistic <= likely <= pessimistic")
    return (optimistic + 4 * likely + pessimistic + 3) // 6


def confidence_pct(task_count):
    return rules.estimate_confidence_pct(task_count)


def padded_range(estimates):
    """(low, high) for a list of per-task day estimates: the sum, and the sum padded by the confidence gap."""
    total = sum(estimates)
    gap = 100 - confidence_pct(len(estimates))
    return total, total + -(-total * gap // 100)


def split_estimate(total_days, parts):
    """Spread a total over `parts` tasks as evenly as possible; earlier tasks take the remainder."""
    if parts < 1:
        raise ValueError("parts must be positive")
    base, extra = divmod(total_days, parts)
    return [base + (1 if i < extra else 0) for i in range(parts)]
