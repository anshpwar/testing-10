#ifndef PK_DEPSET_H
#define PK_DEPSET_H

#include <stddef.h>
#include <stdint.h>

#include "pk_calendar.h"

/* A dependency set is a bitset over task indexes: bit j of set i means "task i depends on task j". */
#define PK_MAX_TASKS 128
#define PK_DEP_WORDS (PK_MAX_TASKS / 64)

typedef struct pk_depset {
    int32_t nbits;
    uint64_t words[PK_DEP_WORDS];
} pk_depset;

size_t pk_depset_sizeof(void);

int pk_dep_init(pk_depset *set, int32_t nbits);
int pk_dep_set(pk_depset *set, int32_t bit);
int pk_dep_unset(pk_depset *set, int32_t bit);

/* 1 when the bit is set, 0 when it is clear, negative on error. */
int pk_dep_test(const pk_depset *set, int32_t bit);

/* Number of bits set. */
int pk_dep_count(const pk_depset *set);

/* dst |= src; both sets must be the same size. Returns the number of bits that were newly set. */
int pk_dep_union(pk_depset *dst, const pk_depset *src);

/* Lowest set bit at or after `from`, or -1 when there is none. */
int pk_dep_next(const pk_depset *set, int32_t from);

/* Transitive closure over `n` sets in place (Warshall). Returns PK_ERR_CYCLE when some task ends up depending on
 * itself; the sets are still closed in that case. */
int pk_dep_closure(pk_depset *sets, int32_t n);

#endif
