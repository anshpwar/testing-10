PY ?= python3
CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2 -fPIC
CFLAGS += -Ic/include

UNAME := $(shell uname)
ifeq ($(UNAME),Darwin)
LIBEXT := dylib
SHARED := -dynamiclib
else
LIBEXT := so
SHARED := -shared
endif

LIB := build/libplanwork.$(LIBEXT)
SRCS := $(wildcard c/src/*.c)
HDRS := $(wildcard c/include/*.h)
TESTS := $(patsubst c/tests/%.c,build/%,$(wildcard c/tests/test_*.c))

.PHONY: build test test-c clean

build: $(LIB)

$(LIB): $(SRCS) $(HDRS)
	@mkdir -p build
	$(CC) $(CFLAGS) $(SHARED) -o $@ $(SRCS)

build/test_%: c/tests/test_%.c $(SRCS) $(HDRS) c/tests/check.h
	@mkdir -p build
	$(CC) $(CFLAGS) -Ic/tests -o $@ $< $(SRCS)

test-c: $(TESTS)
	@for t in $(TESTS); do echo "== $$t"; $$t || exit 1; done

test: test-c build
	$(PY) manage.py test tests --settings=plansite.settings.test --noinput

clean:
	rm -rf build
