#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
src=firmware/components/starter_outputs
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
"${CC:-cc}" -std=c11 -Wall -Wextra -Werror -pedantic -I"$src/include" \
    "$src/panel_controls.c" "$src/starter_outputs.c" "$src/onboard_voltage.c" \
    verification/controller-contact-review.c -o "$build/contact-review"
"$build/contact-review"
