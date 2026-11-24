# R4 assembly with locally fitted relays

Upload this directory’s matching main-gerbers.zip, main-BOM.csv and main-CPL.csv. K1/K2 are intentionally unpopulated by JLC; J30/J35 remain factory-fitted. The PCB is unchanged from pcb-r4.

Per main board: **62 JLC BOM lines, 224 factory placements, 13 hand-fitted parts**. Buy exact Omron G5RL-1-E-HR DC5 relays locally: 5 V coil, eight-pin SPDT. Four relays are needed for two assembled boards.

Regenerate with `python3 tools/prepare_local_relay_assembly.py`. The script checks the validated full-release hashes and proves that only K1/K2 were omitted; remaining BOM rows and CPL coordinates stay identical. assembly-variant.json records source and output hashes. The full factory-relay R4 bundle remains separate.

JLC’s live ordering flow reported 62/62 matched parts after the relay omission. Review all selection checkboxes as well as matching status: J40 and FB1/FB2/R42 were initially unchecked and have to remain selected. Supplier placement approval remains required; no software check certifies physical switching, insulation or thermal behavior.
