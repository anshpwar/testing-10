#include <stdint.h>

#include "check.h"
#include "pk_calendar.h"

/* 2025-01-13 (a Monday) as a day number. */
#define MON_2025_01_13 20101

static pk_calendar make(void) {
    pk_calendar cal;
    CHECK_EQ(pk_calendar_init(&cal, PK_WORKWEEK_MON_FRI), PK_OK);
    return cal;
}

int main(void) {
    pk_calendar cal = make();
    int32_t out = -1;

    /* layout and weekday arithmetic */
    CHECK_EQ(pk_calendar_sizeof(), sizeof(pk_calendar));
    CHECK_EQ(pk_calendar_sizeof(), 264);
    CHECK_EQ(pk_weekday(0), PK_THU);
    CHECK_EQ(pk_weekday(MON_2025_01_13), PK_MON);
    CHECK_EQ(pk_weekday(MON_2025_01_13 + 5), PK_SAT);
    CHECK_EQ(pk_weekday(-1), PK_ERR_RANGE);

    /* init validation */
    CHECK_EQ(pk_calendar_init(&cal, 0), PK_ERR_ARG);
    CHECK_EQ(pk_calendar_init(NULL, PK_WORKWEEK_MON_FRI), PK_ERR_ARG);
    CHECK_EQ(pk_calendar_init(&cal, 0x80), PK_ERR_ARG);
    cal = make();

    /* working days */
    CHECK_EQ(pk_is_workday(&cal, MON_2025_01_13), 1);
    CHECK_EQ(pk_is_workday(&cal, MON_2025_01_13 + 4), 1);
    CHECK_EQ(pk_is_workday(&cal, MON_2025_01_13 + 5), 0);
    CHECK_EQ(pk_is_workday(&cal, MON_2025_01_13 + 6), 0);
    CHECK_EQ(pk_is_workday(NULL, 5), PK_ERR_ARG);

    /* holidays are kept sorted and unique */
    CHECK_EQ(pk_calendar_add_holiday(&cal, MON_2025_01_13 + 3), PK_OK);
    CHECK_EQ(pk_calendar_add_holiday(&cal, MON_2025_01_13 + 1), PK_OK);
    CHECK_EQ(pk_calendar_add_holiday(&cal, MON_2025_01_13 + 3), PK_OK);
    CHECK_EQ(cal.holiday_count, 2);
    CHECK_EQ(cal.holidays[0], MON_2025_01_13 + 1);
    CHECK_EQ(cal.holidays[1], MON_2025_01_13 + 3);
    CHECK_EQ(pk_is_workday(&cal, MON_2025_01_13 + 1), 0);
    CHECK_EQ(pk_calendar_add_holiday(&cal, -4), PK_ERR_RANGE);

    /* the holiday table has a fixed capacity */
    cal = make();
    for (int32_t i = 0; i < PK_MAX_HOLIDAYS; i++) {
        CHECK_EQ(pk_calendar_add_holiday(&cal, 1000 + i), PK_OK);
    }
    CHECK_EQ(pk_calendar_add_holiday(&cal, 5000), PK_ERR_FULL);
    CHECK_EQ(pk_calendar_add_holiday(&cal, 1010), PK_OK);

    /* next workday */
    cal = make();
    CHECK_EQ(pk_next_workday(&cal, MON_2025_01_13 + 5, &out), PK_OK);
    CHECK_EQ(out, MON_2025_01_13 + 7);
    CHECK_EQ(pk_next_workday(&cal, MON_2025_01_13, &out), PK_OK);
    CHECK_EQ(out, MON_2025_01_13);
    CHECK_EQ(pk_next_workday(&cal, MON_2025_01_13, NULL), PK_ERR_ARG);

    CHECK_DONE();
}
