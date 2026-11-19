#!/bin/sh
# Run from the repository root with KiCad 10 and the pinned GerberTools comparator.
set -eu
if [ "$#" -ne 1 ]; then
    echo "Usage: tools/verify_integrated_prototype.sh /path/to/gerbertools-compare" >&2
    exit 2
fi
driver=$1
test -x "$driver"
main=hardware/main-integrated
board="$main/pump-controller-integrated.kicad_pcb"
checks="$main/checks"
panel=hardware/panel-rev-f/pump-panel-rev-f.kicad_pcb
kicad_python=${KICAD_PYTHON:-.tools/kicad-python}
cam_python=${CAM_PYTHON:-.tools/cam-validation-env/bin/python}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
python3 tools/validate_main_rev_e.py --board "$board" --source design/main-integrated.json --output "$checks"
"$kicad_python" tools/check_compact_bypasses.py --board "$board" --output "$checks/bypass-routing.json"
"$kicad_python" tools/check_main_panel_rev_e_integration.py --control-variant integrated \
    --main-board "$board" --main-source design/main-integrated.json --main-summary "$checks/independent-summary.json" \
    --panel-board "$panel" --panel-source design/panel-rev-f.json --require-frozen-main --output "$work"
cp "$work/integration-review.json" "$checks/panel-integration.json"
python3 tools/check_integrated_equivalence.py
python3 tools/check_integrated_cabinet.py
"$kicad_python" tools/check_integrated_receiver_routes.py
"$kicad_python" tools/check_usb_service.py --integrated
python3 tools/export_main_rev_e.py --integrated
"$cam_python" tools/check_main_rev_e_gerbers.py --integrated
python3 tools/package_main_rev_e.py --integrated
if ! "$cam_python" tools/cam/check_archives.py "$driver" --boards integrated panel \
    --output "$checks/gerber-copper-connectivity.json"; then
    rm -f "$main"/pump-controller-integrated-r4-*-prototype.zip "$main/package-manifest.json" \
          "$checks/gerber-copper-connectivity.json"
    exit 1
fi
