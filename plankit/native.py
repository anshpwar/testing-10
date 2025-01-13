"""ctypes bindings for the C working-calendar and dependency-bitset helper (build/libplanwork).

Structure layouts and constants mirror c/include/pk_calendar.h and c/include/pk_depset.h. The library exports
pk_calendar_sizeof / pk_depset_sizeof so tests can detect layout drift between the two sides.
"""
import ctypes
import datetime as dt
import os
import pathlib
import sys

OK = 0
ERR_ARG = -1
ERR_RANGE = -2
ERR_FULL = -3
ERR_CYCLE = -4
ERR_NOWORK = -5

ERROR_NAMES = {
    ERR_ARG: "invalid argument",
    ERR_RANGE: "day or index out of range",
    ERR_FULL: "table is full",
    ERR_CYCLE: "dependency cycle",
    ERR_NOWORK: "calendar has no working day",
}

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)
WORKWEEK_MON_FRI = 0x1F

MAX_HOLIDAYS = 64
MAX_TASKS = 128
DEP_WORDS = MAX_TASKS // 64

EPOCH_ORDINAL = dt.date(1970, 1, 1).toordinal()
DAY_MAX = 2932896

ROOT = pathlib.Path(__file__).resolve().parent.parent


class NativeError(Exception):
    """A negative status code returned by the C library."""

    def __init__(self, code):
        self.code = code
        super().__init__(f"{ERROR_NAMES.get(code, 'native error')} ({code})")


class PkCalendar(ctypes.Structure):
    _fields_ = [
        ("workweek", ctypes.c_uint8),
        ("holiday_count", ctypes.c_int32),
        ("holidays", ctypes.c_int32 * MAX_HOLIDAYS),
    ]


class PkDepset(ctypes.Structure):
    _fields_ = [
        ("nbits", ctypes.c_int32),
        ("words", ctypes.c_uint64 * DEP_WORDS),
    ]


def library_path():
    override = os.environ.get("PLANKIT_LIB")
    if override:
        return pathlib.Path(override)
    ext = "dylib" if sys.platform == "darwin" else "so"
    return ROOT / "build" / f"libplanwork.{ext}"


_LIB = None


def _declare(lib):
    i32, u8, sz = ctypes.c_int32, ctypes.c_uint8, ctypes.c_size_t
    pcal, pset, pi32 = ctypes.POINTER(PkCalendar), ctypes.POINTER(PkDepset), ctypes.POINTER(ctypes.c_int32)
    specs = {
        "pk_calendar_sizeof": ([], sz),
        "pk_depset_sizeof": ([], sz),
        "pk_calendar_init": ([pcal, u8], ctypes.c_int),
        "pk_calendar_add_holiday": ([pcal, i32], ctypes.c_int),
        "pk_weekday": ([i32], ctypes.c_int),
        "pk_is_workday": ([pcal, i32], ctypes.c_int),
        "pk_next_workday": ([pcal, i32, pi32], ctypes.c_int),
        "pk_add_workdays": ([pcal, i32, i32, pi32], ctypes.c_int),
        "pk_workdays_between": ([pcal, i32, i32, pi32], ctypes.c_int),
        "pk_finish_day": ([pcal, i32, i32, pi32], ctypes.c_int),
        "pk_dep_init": ([pset, i32], ctypes.c_int),
        "pk_dep_set": ([pset, i32], ctypes.c_int),
        "pk_dep_unset": ([pset, i32], ctypes.c_int),
        "pk_dep_test": ([pset, i32], ctypes.c_int),
        "pk_dep_count": ([pset], ctypes.c_int),
        "pk_dep_union": ([pset, pset], ctypes.c_int),
        "pk_dep_next": ([pset, i32], ctypes.c_int),
        "pk_dep_closure": ([pset, i32], ctypes.c_int),
    }
    for name, (argtypes, restype) in specs.items():
        fn = getattr(lib, name)
        fn.argtypes = argtypes
        fn.restype = restype
    return lib


def library():
    """Load the shared library once; raises OSError if `make build` has not run."""
    global _LIB
    if _LIB is None:
        _LIB = _declare(ctypes.CDLL(str(library_path())))
    return _LIB


def _check(rc):
    if rc < 0:
        raise NativeError(rc)
    return rc


def calendar_sizeof():
    return library().pk_calendar_sizeof()


def depset_sizeof():
    return library().pk_depset_sizeof()


# ------------------------------------------------------------------------------ day numbers
def to_day(date):
    """Day number (days since 1970-01-01) of a date."""
    return date.toordinal() - EPOCH_ORDINAL


def from_day(day):
    return dt.date.fromordinal(day + EPOCH_ORDINAL)


# ------------------------------------------------------------------------------ calendar
def make_calendar(workweek=WORKWEEK_MON_FRI, holidays=()):
    """Build a PkCalendar from a weekday mask and an iterable of dates."""
    cal = PkCalendar()
    lib = library()
    _check(lib.pk_calendar_init(ctypes.byref(cal), workweek))
    for date in holidays:
        _check(lib.pk_calendar_add_holiday(ctypes.byref(cal), to_day(date)))
    return cal


def weekday(date):
    return _check(library().pk_weekday(to_day(date)))


def is_workday(cal, date):
    return bool(_check(library().pk_is_workday(ctypes.byref(cal), to_day(date))))


def next_workday(cal, date):
    out = ctypes.c_int32()
    _check(library().pk_next_workday(ctypes.byref(cal), to_day(date), ctypes.byref(out)))
    return from_day(out.value)


def add_workdays(cal, date, n):
    """Date reached after n working days (n == 0: first working day on or after `date`)."""
    out = ctypes.c_int32()
    _check(library().pk_add_workdays(ctypes.byref(cal), to_day(date), n, ctypes.byref(out)))
    return from_day(out.value)


def workdays_between(cal, start, end):
    """Working days in [start, end); negative when end precedes start."""
    out = ctypes.c_int32()
    _check(library().pk_workdays_between(ctypes.byref(cal), to_day(start), to_day(end), ctypes.byref(out)))
    return out.value


def finish_day(cal, start, duration):
    """Last working day of a task of `duration` working days beginning on or after `start`."""
    out = ctypes.c_int32()
    _check(library().pk_finish_day(ctypes.byref(cal), to_day(start), duration, ctypes.byref(out)))
    return from_day(out.value)


# ------------------------------------------------------------------------------ dependency sets
def make_depsets(n, edges):
    """Array of n depsets where edges are (task_index, depends_on_index) pairs."""
    lib = library()
    sets = (PkDepset * max(n, 1))()
    for i in range(n):
        _check(lib.pk_dep_init(ctypes.byref(sets[i]), n))
    for task, dep in edges:
        _check(lib.pk_dep_set(ctypes.byref(sets[task]), dep))
    return sets


def depset_members(depset):
    lib = library()
    members, bit = [], lib.pk_dep_next(ctypes.byref(depset), 0)
    while bit >= 0:
        members.append(bit)
        bit = lib.pk_dep_next(ctypes.byref(depset), bit + 1)
    return members


def dep_count(depset):
    return _check(library().pk_dep_count(ctypes.byref(depset)))


def closure(n, edges):
    """Transitive dependencies of every task as a list of sorted index lists.

    Raises NativeError(ERR_CYCLE) when the edges contain a cycle.
    """
    sets = make_depsets(n, edges)
    _check(library().pk_dep_closure(sets, n))
    return [depset_members(sets[i]) for i in range(n)]
