#include <string.h>

#include "pk_depset.h"

size_t pk_depset_sizeof(void) {
    return sizeof(pk_depset);
}

static int bit_ok(const pk_depset *set, int32_t bit) {
    return bit >= 0 && bit < set->nbits;
}

int pk_dep_init(pk_depset *set, int32_t nbits) {
    if (set == NULL || nbits < 0 || nbits > PK_MAX_TASKS) {
        return PK_ERR_ARG;
    }
    memset(set, 0, sizeof(*set));
    set->nbits = nbits;
    return PK_OK;
}

int pk_dep_set(pk_depset *set, int32_t bit) {
    if (set == NULL || !bit_ok(set, bit)) {
        return PK_ERR_RANGE;
    }
    set->words[bit / 64] |= (uint64_t)1 << (bit % 64);
    return PK_OK;
}

int pk_dep_unset(pk_depset *set, int32_t bit) {
    if (set == NULL || !bit_ok(set, bit)) {
        return PK_ERR_RANGE;
    }
    set->words[bit / 64] &= ~((uint64_t)1 << (bit % 64));
    return PK_OK;
}

int pk_dep_test(const pk_depset *set, int32_t bit) {
    if (set == NULL || !bit_ok(set, bit)) {
        return PK_ERR_RANGE;
    }
    return (int)((set->words[bit / 64] >> (bit % 64)) & 1);
}

static int popcount64(uint64_t w) {
    int n = 0;
    while (w != 0) {
        w &= w - 1;
        n++;
    }
    return n;
}

int pk_dep_count(const pk_depset *set) {
    int n = 0;
    if (set == NULL) {
        return PK_ERR_ARG;
    }
    for (int i = 0; i < PK_DEP_WORDS; i++) {
        n += popcount64(set->words[i]);
    }
    return n;
}

int pk_dep_union(pk_depset *dst, const pk_depset *src) {
    int added = 0;
    if (dst == NULL || src == NULL || dst->nbits != src->nbits) {
        return PK_ERR_ARG;
    }
    for (int i = 0; i < PK_DEP_WORDS; i++) {
        uint64_t fresh = src->words[i] & ~dst->words[i];
        added += popcount64(fresh);
        dst->words[i] |= src->words[i];
    }
    return added;
}

int pk_dep_next(const pk_depset *set, int32_t from) {
    if (set == NULL) {
        return PK_ERR_ARG;
    }
    for (int32_t b = from < 0 ? 0 : from; b < set->nbits; b++) {
        if ((set->words[b / 64] >> (b % 64)) & 1) {
            return b;
        }
    }
    return -1;
}

int pk_dep_closure(pk_depset *sets, int32_t n) {
    int cyclic = 0;
    if (sets == NULL || n < 0 || n > PK_MAX_TASKS) {
        return PK_ERR_ARG;
    }
    for (int32_t i = 0; i < n; i++) {
        if (sets[i].nbits != n) {
            return PK_ERR_ARG;
        }
    }
    for (int32_t k = 0; k < n; k++) {
        for (int32_t i = 0; i < n; i++) {
            if (pk_dep_test(&sets[i], k) == 1) {
                pk_dep_union(&sets[i], &sets[k]);
            }
        }
    }
    for (int32_t i = 0; i < n; i++) {
        if (pk_dep_test(&sets[i], i) == 1) {
            cyclic = 1;
        }
    }
    return cyclic ? PK_ERR_CYCLE : PK_OK;
}
