#!/bin/sh
set -eu
cli=${KICAD_CLI:-kicad-cli}
board=hardware/pump-controller-rev-b.kicad_pcb
"$cli" pcb export svg --layers F.Cu,F.Silkscreen,F.Fab,Edge.Cuts --exclude-drawing-sheet --page-size-mode 2 --mode-single -o hardware/previews/main-top.svg "$board"
"$cli" pcb export svg --layers B.Cu,B.Silkscreen,B.Fab,Edge.Cuts --mirror --exclude-drawing-sheet --page-size-mode 2 --mode-single -o hardware/previews/main-bottom.svg "$board"
"$cli" pcb export svg --layers F.Fab,Edge.Cuts --sketch-pads-on-fab-layers --exclude-drawing-sheet --page-size-mode 2 --mode-single -o hardware/previews/assembly-front.svg "$board"
"$cli" pcb export svg --layers B.Fab,Edge.Cuts --sketch-pads-on-fab-layers --mirror --exclude-drawing-sheet --page-size-mode 2 --mode-single -o hardware/previews/assembly-back.svg "$board"
"$cli" pcb export svg --layers In1.Cu,Edge.Cuts --exclude-drawing-sheet --page-size-mode 2 --mode-single -o hardware/previews/inner-1.svg "$board"
"$cli" pcb export svg --layers In2.Cu,Edge.Cuts --exclude-drawing-sheet --page-size-mode 2 --mode-single -o hardware/previews/inner-2.svg "$board"
