#include <string.h>

#include "pk_calendar.h"

size_t pk_calendar_sizeof(void) {
    return sizeof(pk_calendar);
}

static int day_ok(int32_t day) {
    return day >= PK_DAY_MIN && day <= PK_DAY_MAX;
}

int pk_calendar_init(pk_calendar *cal, uint8_t workweek) {
    if (cal == NULL || workweek == 0 || (workweek & 0x80) != 0) {
        return PK_ERR_ARG;
    }
    memset(cal, 0, sizeof(*cal));
    cal->workweek = workweek;
    return PK_OK;
}

int pk_calendar_add_holiday(pk_calendar *cal, int32_t day) {
    int32_t pos = 0;
    if (cal == NULL) {
        return PK_ERR_ARG;
    }
    if (!day_ok(day)) {
        return PK_ERR_RANGE;
    }
    while (pos < cal->holiday_count && cal->holidays[pos] < day) {
        pos++;
    }
    if (pos < cal->holiday_count && cal->holidays[pos] == day) {
        return PK_OK;
    }
    if (cal->holiday_count >= PK_MAX_HOLIDAYS) {
        return PK_ERR_FULL;
    }
    memmove(&cal->holidays[pos + 1], &cal->holidays[pos], (size_t)(cal->holiday_count - pos) * sizeof(int32_t));
    cal->holidays[pos] = day;
    cal->holiday_count++;
    return PK_OK;
}

int pk_weekday(int32_t day) {
    if (!day_ok(day)) {
        return PK_ERR_RANGE;
    }
    return (int)((day + 3) % 7);
}

static int is_holiday(const pk_calendar *cal, int32_t day) {
    int32_t lo = 0;
    int32_t hi = cal->holiday_count - 1;
    while (lo <= hi) {
        int32_t mid = lo + (hi - lo) / 2;
        if (cal->holidays[mid] == day) {
            return 1;
        }
        if (cal->holidays[mid] < day) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return 0;
}

int pk_is_workday(const pk_calendar *cal, int32_t day) {
    int wd;
    if (cal == NULL) {
        return PK_ERR_ARG;
    }
    wd = pk_weekday(day);
    if (wd < 0) {
        return wd;
    }
    if (((cal->workweek >> wd) & 1) == 0) {
        return 0;
    }
    return is_holiday(cal, day) ? 0 : 1;
}

int pk_next_workday(const pk_calendar *cal, int32_t day, int32_t *out) {
    if (cal == NULL || out == NULL) {
        return PK_ERR_ARG;
    }
    if (!day_ok(day)) {
        return PK_ERR_RANGE;
    }
    /* A calendar with a working weekday always finds a day within a year unless holidays cover it all. */
    for (int32_t d = day; d <= PK_DAY_MAX && d - day <= 800; d++) {
        if (pk_is_workday(cal, d) == 1) {
            *out = d;
            return PK_OK;
        }
    }
    return PK_ERR_NOWORK;
}

int pk_add_workdays(const pk_calendar *cal, int32_t start, int32_t n, int32_t *out) {
    int32_t day = start;
    int32_t left;
    int32_t step;
    if (cal == NULL || out == NULL) {
        return PK_ERR_ARG;
    }
    if (!day_ok(start)) {
        return PK_ERR_RANGE;
    }
    if (n == 0) {
        return pk_next_workday(cal, start, out);
    }
    step = n > 0 ? 1 : -1;
    left = n > 0 ? n : -n;
    while (left > 0) {
        day += step;
        if (!day_ok(day)) {
            return PK_ERR_RANGE;
        }
        if (pk_is_workday(cal, day) == 1) {
            left--;
        }
    }
    *out = day;
    return PK_OK;
}

int pk_workdays_between(const pk_calendar *cal, int32_t from, int32_t to, int32_t *out) {
    int32_t lo;
    int32_t hi;
    int32_t count = 0;
    if (cal == NULL || out == NULL) {
        return PK_ERR_ARG;
    }
    if (!day_ok(from) || !day_ok(to)) {
        return PK_ERR_RANGE;
    }
    lo = from < to ? from : to;
    hi = from < to ? to : from;
    for (int32_t d = lo; d < hi; d++) {
        if (pk_is_workday(cal, d) == 1) {
            count++;
        }
    }
    *out = from <= to ? count : -count;
    return PK_OK;
}

int pk_finish_day(const pk_calendar *cal, int32_t start, int32_t duration, int32_t *out) {
    int32_t first;
    int rc;
    if (duration < 1) {
        return PK_ERR_ARG;
    }
    rc = pk_next_workday(cal, start, &first);
    if (rc != PK_OK) {
        return rc;
    }
    return pk_add_workdays(cal, first, duration - 1, out);
}
