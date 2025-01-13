#ifndef PK_CALENDAR_H
#define PK_CALENDAR_H

#include <stddef.h>
#include <stdint.h>

/* Status codes shared by every pk_* function. Zero is success, negative values are errors. */
#define PK_OK 0
#define PK_ERR_ARG (-1)
#define PK_ERR_RANGE (-2)
#define PK_ERR_FULL (-3)
#define PK_ERR_CYCLE (-4)
#define PK_ERR_NOWORK (-5)

/* Day numbers count days since 1970-01-01 (day 0 was a Thursday). */
#define PK_DAY_MIN 0
#define PK_DAY_MAX 2932896 /* 9999-12-31 */

/* Weekday numbers: Monday is 0 and Sunday is 6; a workweek mask has bit n set when weekday n is a working day. */
#define PK_MON 0
#define PK_TUE 1
#define PK_WED 2
#define PK_THU 3
#define PK_FRI 4
#define PK_SAT 5
#define PK_SUN 6
#define PK_WORKWEEK_MON_FRI 0x1F

#define PK_MAX_HOLIDAYS 64

/* Working calendar: a weekly pattern plus a sorted list of single-day holidays. */
typedef struct pk_calendar {
    uint8_t workweek;
    int32_t holiday_count;
    int32_t holidays[PK_MAX_HOLIDAYS];
} pk_calendar;

size_t pk_calendar_sizeof(void);

/* Reset the calendar to `workweek` (non-zero, only the low seven bits) and no holidays. */
int pk_calendar_init(pk_calendar *cal, uint8_t workweek);

/* Insert a holiday keeping the list sorted; adding the same day twice is a no-op. */
int pk_calendar_add_holiday(pk_calendar *cal, int32_t day);

/* Weekday of a day number (0 = Monday), or a negative status for an out-of-range day. */
int pk_weekday(int32_t day);

/* 1 when `day` is a working day, 0 when it is not, negative on error. */
int pk_is_workday(const pk_calendar *cal, int32_t day);

/* First working day on or after `day`. */
int pk_next_workday(const pk_calendar *cal, int32_t day, int32_t *out);

/* Move `n` working days from `start`. With n == 0 the result is the first working day on or after start; a negative
 * n walks backwards. Non-working days are skipped and never counted. */
int pk_add_workdays(const pk_calendar *cal, int32_t start, int32_t n, int32_t *out);

/* Number of working days in the half-open interval [from, to); negative when `to` is before `from`. */
int pk_workdays_between(const pk_calendar *cal, int32_t from, int32_t to, int32_t *out);

/* Last day of work that takes `duration` (>= 1) working days when it begins on or after `start`. */
int pk_finish_day(const pk_calendar *cal, int32_t start, int32_t duration, int32_t *out);

#endif
