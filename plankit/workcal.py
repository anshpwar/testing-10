"""Working calendar: a weekly pattern plus holidays, backed by the C day arithmetic in native.py."""
import datetime as dt

from . import native


class WorkCalendar:
    """Immutable view of a project calendar. Dates in, dates out; the C library only ever sees day numbers."""

    def __init__(self, workweek=native.WORKWEEK_MON_FRI, holidays=()):
        self.workweek = workweek
        self.holidays = tuple(sorted(set(holidays)))
        if len(self.holidays) > native.MAX_HOLIDAYS:
            raise ValueError(f"at most {native.MAX_HOLIDAYS} holidays per calendar")
        self._cal = native.make_calendar(workweek, self.holidays)

    @classmethod
    def from_weekdays(cls, weekdays, holidays=()):
        """Calendar whose working days are the given weekday numbers (Monday is 0)."""
        mask = 0
        for wd in weekdays:
            mask |= 1 << wd
        return cls(mask, holidays)

    def working_weekdays(self):
        return [wd for wd in range(7) if self.workweek >> wd & 1]

    def is_workday(self, date):
        return native.is_workday(self._cal, date)

    def next_workday(self, date):
        return native.next_workday(self._cal, date)

    def add(self, date, n):
        """Date after n working days; n == 0 gives the first working day on or after `date`."""
        return native.add_workdays(self._cal, date, n)

    def between(self, start, end):
        """Working days in [start, end); negative when end is earlier than start."""
        return native.workdays_between(self._cal, start, end)

    def span(self, start, duration):
        """(first, last) working days of a task of `duration` days that cannot begin before `start`."""
        first = self.next_workday(start)
        return first, native.finish_day(self._cal, first, duration)

    def working_dates(self, start, end):
        """Every working date in [start, end)."""
        out, day = [], start
        while day < end:
            if self.is_workday(day):
                out.append(day)
            day += dt.timedelta(days=1)
        return out
