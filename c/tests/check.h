#ifndef PK_CHECK_H
#define PK_CHECK_H

#include <stdio.h>

static int g_checks = 0;
static int g_failures = 0;

#define CHECK(cond)                                                            \
    do {                                                                       \
        g_checks++;                                                            \
        if (!(cond)) {                                                         \
            g_failures++;                                                      \
            fprintf(stderr, "  FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);  \
        }                                                                      \
    } while (0)

#define CHECK_EQ(actual, expected)                                             \
    do {                                                                       \
        long long a_ = (long long)(actual);                                    \
        long long e_ = (long long)(expected);                                  \
        g_checks++;                                                            \
        if (a_ != e_) {                                                        \
            g_failures++;                                                      \
            fprintf(stderr, "  FAIL %s:%d: %s == %lld, expected %lld\n",       \
                    __FILE__, __LINE__, #actual, a_, e_);                      \
        }                                                                      \
    } while (0)

#define CHECK_DONE()                                                           \
    do {                                                                       \
        printf("  %d checks, %d failures\n", g_checks, g_failures);            \
        return g_failures == 0 ? 0 : 1;                                        \
    } while (0)

#endif
