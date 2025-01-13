#include <stdint.h>

#include "check.h"
#include "pk_calendar.h"

#define MON 20101 /* 2025-01-13 */

int main(void) {
    pk_calendar cal;
    int32_t out = -1;

    pk_calendar_init(&cal, PK_WORKWEEK_MON_FRI);

    /* adding workdays skips weekends */
    CHECK_EQ(pk_add_workdays(&cal, MON, 0, &out), PK_OK);
    CHECK_EQ(out, MON);
    CHECK_EQ(pk_add_workdays(&cal, MON, 1, &out), PK_OK);
    CHECK_EQ(out, MON + 1);
    CHECK_EQ(pk_add_workdays(&cal, MON, 5, &out), PK_OK);
    CHECK_EQ(out, MON + 7);
    CHECK_EQ(pk_add_workdays(&cal, MON + 4, 1, &out), PK_OK);
    CHECK_EQ(out, MON + 7);
    CHECK_EQ(pk_add_workdays(&cal, MON + 5, 0, &out), PK_OK);
    CHECK_EQ(out, MON + 7);
    CHECK_EQ(pk_add_workdays(&cal, MON, 10, &out), PK_OK);
    CHECK_EQ(out, MON + 14);

    /* walking backwards */
    CHECK_EQ(pk_add_workdays(&cal, MON + 7, -1, &out), PK_OK);
    CHECK_EQ(out, MON + 4);
    CHECK_EQ(pk_add_workdays(&cal, MON + 14, -10, &out), PK_OK);
    CHECK_EQ(out, MON);
    CHECK_EQ(pk_add_workdays(&cal, 2, -5, &out), PK_ERR_RANGE);

    /* holidays are skipped too */
    pk_calendar_add_holiday(&cal, MON + 2);
    CHECK_EQ(pk_add_workdays(&cal, MON, 2, &out), PK_OK);
    CHECK_EQ(out, MON + 3);
    CHECK_EQ(pk_add_workdays(&cal, MON + 3, -1, &out), PK_OK);
    CHECK_EQ(out, MON + 1);

    /* counting workdays in [from, to) */
    pk_calendar_init(&cal, PK_WORKWEEK_MON_FRI);
    CHECK_EQ(pk_workdays_between(&cal, MON, MON + 7, &out), PK_OK);
    CHECK_EQ(out, 5);
    CHECK_EQ(pk_workdays_between(&cal, MON, MON, &out), PK_OK);
    CHECK_EQ(out, 0);
    CHECK_EQ(pk_workdays_between(&cal, MON + 7, MON, &out), PK_OK);
    CHECK_EQ(out, -5);
    CHECK_EQ(pk_workdays_between(&cal, MON + 5, MON + 7, &out), PK_OK);
    CHECK_EQ(out, 0);
    CHECK_EQ(pk_workdays_between(&cal, -1, MON, &out), PK_ERR_RANGE);

    /* finish day of a task */
    CHECK_EQ(pk_finish_day(&cal, MON, 1, &out), PK_OK);
    CHECK_EQ(out, MON);
    CHECK_EQ(pk_finish_day(&cal, MON, 5, &out), PK_OK);
    CHECK_EQ(out, MON + 4);
    CHECK_EQ(pk_finish_day(&cal, MON, 6, &out), PK_OK);
    CHECK_EQ(out, MON + 7);
    CHECK_EQ(pk_finish_day(&cal, MON + 5, 2, &out), PK_OK);
    CHECK_EQ(out, MON + 8);
    CHECK_EQ(pk_finish_day(&cal, MON, 0, &out), PK_ERR_ARG);

    /* a calendar of only the weekend plus a one-day week */
    pk_calendar_init(&cal, 1 << PK_WED);
    CHECK_EQ(pk_add_workdays(&cal, MON, 2, &out), PK_OK);
    CHECK_EQ(out, MON + 9);

    CHECK_DONE();
}
