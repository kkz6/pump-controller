#!/bin/sh
set -eu

components=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
outputs="$components/starter_outputs"
leds="$components/command_leds"
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
for test in "$outputs/tests/panel_controls_test.c" "$outputs/tests/starter_outputs_test.c" "$leds/tests/command_leds_test.c"; do
    program="$build/$(basename "$test" .c)"
    "${CC:-cc}" -std=c11 -Wall -Wextra -Werror -pedantic -I"$outputs/include" -I"$leds/include" \
        "$outputs/panel_controls.c" "$outputs/starter_outputs.c" "$leds/command_leds.c" "$test" -o "$program"
    "$program"
    printf '%s passed\n' "$(basename "$program")"
done
