#include <stdint.h>

#include "check.h"
#include "pk_depset.h"

int main(void) {
    pk_depset a;
    pk_depset b;
    pk_depset chain[4];

    CHECK_EQ(pk_depset_sizeof(), sizeof(pk_depset));
    CHECK_EQ(pk_depset_sizeof(), 24);

    /* init, set, test, unset */
    CHECK_EQ(pk_dep_init(&a, 70), PK_OK);
    CHECK_EQ(pk_dep_init(NULL, 3), PK_ERR_ARG);
    CHECK_EQ(pk_dep_init(&b, PK_MAX_TASKS + 1), PK_ERR_ARG);
    CHECK_EQ(pk_dep_set(&a, 0), PK_OK);
    CHECK_EQ(pk_dep_set(&a, 64), PK_OK);
    CHECK_EQ(pk_dep_set(&a, 69), PK_OK);
    CHECK_EQ(pk_dep_set(&a, 70), PK_ERR_RANGE);
    CHECK_EQ(pk_dep_set(&a, -1), PK_ERR_RANGE);
    CHECK_EQ(pk_dep_test(&a, 64), 1);
    CHECK_EQ(pk_dep_test(&a, 63), 0);
    CHECK_EQ(pk_dep_count(&a), 3);
    CHECK_EQ(pk_dep_unset(&a, 64), PK_OK);
    CHECK_EQ(pk_dep_test(&a, 64), 0);
    CHECK_EQ(pk_dep_count(&a), 2);

    /* iteration */
    CHECK_EQ(pk_dep_next(&a, 0), 0);
    CHECK_EQ(pk_dep_next(&a, 1), 69);
    CHECK_EQ(pk_dep_next(&a, 70), -1);

    /* union reports newly set bits and demands equal sizes */
    pk_dep_init(&b, 70);
    pk_dep_set(&b, 0);
    pk_dep_set(&b, 5);
    CHECK_EQ(pk_dep_union(&b, &a), 1);
    CHECK_EQ(pk_dep_count(&b), 3);
    CHECK_EQ(pk_dep_union(&b, &a), 0);
    pk_dep_init(&a, 10);
    CHECK_EQ(pk_dep_union(&b, &a), PK_ERR_ARG);

    /* transitive closure of the chain 3 -> 2 -> 1 -> 0 */
    for (int i = 0; i < 4; i++) {
        pk_dep_init(&chain[i], 4);
    }
    pk_dep_set(&chain[3], 2);
    pk_dep_set(&chain[2], 1);
    pk_dep_set(&chain[1], 0);
    CHECK_EQ(pk_dep_closure(chain, 4), PK_OK);
    CHECK_EQ(pk_dep_count(&chain[3]), 3);
    CHECK_EQ(pk_dep_count(&chain[2]), 2);
    CHECK_EQ(pk_dep_count(&chain[1]), 1);
    CHECK_EQ(pk_dep_count(&chain[0]), 0);
    CHECK_EQ(pk_dep_test(&chain[3], 0), 1);

    /* a cycle is reported once the closure has run */
    pk_dep_set(&chain[0], 3);
    CHECK_EQ(pk_dep_closure(chain, 4), PK_ERR_CYCLE);
    CHECK_EQ(pk_dep_test(&chain[0], 0), 1);

    /* mismatched set sizes are rejected */
    pk_dep_init(&chain[2], 5);
    CHECK_EQ(pk_dep_closure(chain, 4), PK_ERR_ARG);
    CHECK_EQ(pk_dep_closure(NULL, 4), PK_ERR_ARG);

    CHECK_DONE();
}
