"""Check the common-supply circuit against independently exported KiCad pin nets."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from itertools import product

import check_budget_cabinet as budget
from check_integrated_cabinet import ROOT, terminal_nets

FIELD = ROOT / 'hardware/starter-metered-r4'
MAIN = ROOT / 'hardware/main-socketed'
PREVIOUS = ROOT / 'hardware/starter-budget-r4/checks/guard-netlist.xml'


def native():
    cli = os.getenv('KICAD_CLI') or shutil.which('kicad-cli') or str(ROOT / '.tools/kicad-cli')
    tracked = FIELD / 'checks/guard-netlist.xml'
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        budget.check_export(FIELD / (FIELD.name + '.kicad_sch'), tracked, cli, tmp)
        fresh = tmp / 'socketed.xml'
        subprocess.run([cli,'sch','export','netlist','--format','kicadxml','-o',fresh,
                        MAIN / 'pump-controller-integrated.kicad_sch'], check=True)
        main = terminal_nets(fresh)
    source = json.loads((ROOT / 'output/socketed-r4/verification.json').read_text())['boards']['main']
    for path, digest in source['source_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    old, pins = terminal_nets(PREVIOUS), terminal_nets(tracked)
    deleted = {'KV1','KC1'}
    assert set(budget.parts(tracked)) == set(budget.parts(PREVIOUS)) - deleted | {'F3','J1'}
    rename = {'CAB_SUPPLY_L':'AUX_AC_L', 'CAB_SUPPLY_N':'MOTOR_RETURN',
              'OEM_CTRL_L':'FUSED_24', 'OEM_CTRL_N':'CAB_0', 'ALL_SUPPLIES_OK':'AFTER_OL'}
    expected = {k:rename.get(v,v) for k,v in old.items() if k[0] not in deleted}
    expected.update({('F3','1'):'PROTECTED_LINE', ('F3','2'):'AUX_AC_L',
                     ('J1','1'):'AUX_AC_L', ('J1','2'):'MOTOR_RETURN'})
    assert pins == expected
    for n in ('1','2'):
        assert pins['J1',n] == pins['PS2', 'L' if n=='1' else 'N']
    assert pins['S3','OEM-IN']==pins['F2','2'] and pins['XP1','2']==pins['PS2','-V']
    assert pins['S3','OEM-OUT']==pins['S4','OEM-IN'] and pins['S4','OEM-OUT']==pins['S5','OEM-IN']
    for plug, relay in [('J30','K1'), ('J35','K2')]:
        for n,socket_pin in [('1','3'), ('2','4')]:
            assert main[plug,n] == main[relay,socket_pin]
    for plug,pairs in {'J52':('1','2','3'), 'J54':('1','2','4','5')}.items():
        assert all(main[plug,n]==pins[plug,n] for n in pairs)
    assert main['K1','6']==main['KFB1','8']
    assert main['J1','1']==main['F1','1'] and main['J1','2']==main['R42','1']
    assert main['U10','12']==main['R46','2'] and main['U10','11']==main['R48','2']
    assert main['U10','28']==main['U11','23'] and main['U11','6']==main['U3','24']
    return pins


def supplies(circuit):
    results = {}
    for mode, welded in product(('HOST','LOCAL'),(False,True)):
        for loss in ('cabinet','branch','isolator','board','cover'):
            rig=budget.Rig(circuit,budget.Controls(mode=mode))
            rig.run()
            rig.step(weld_a=welded,weld_b=welded,reset='pressed')
            rig.step(**{loss:False})
            local_independent = mode=='LOCAL' and loss=='board'
            assert rig.motor == local_independent
            rig.step(**{loss:True},dwell=True)
            assert rig.motor == local_independent and rig.r.enable == local_independent
        # Downstream open control wire reconnected with a held pickup. No supply
        # supervision or auxiliary STOP interruption occurred on that event.
        rig=budget.Rig(circuit,budget.Controls(mode=mode))
        rig.run()
        rig.step(weld_b=True,start=mode=='LOCAL')
        rig.step(pilot=False)
        assert not rig.motor and rig.r.enable
        rig.step(pilot=True)
        assert rig.motor
        results[mode+('/welded' if welded else '/normal')]='Five settled supply/service sequences passed'
    return results


def main():
    circ = budget.Circuit(native(), FIELD, shared_supply=True)
    trips, states = budget.trip_and_restart_tests(circ)
    report = dict(native_contact_rows=circ.contact_rows, stop_and_overload_cases=trips,
                  recovery_states_checked=states, timed_stop=budget.short_trip_capture(circ),
                  reset=budget.reset_qualification(circ), lead_and_command_faults=budget.release_cases(circ),
                  powers=supplies(circ), fault_limits=budget.boundary_cases(circ),
                  electrical_envelope=budget.electrical_corners(), physical_starter_tested=False,
                  limitations=['Common rail fully drops for a sustained shared supply outage. Short dips and supply hold-up require measurement.',
                               'Downstream OEM pilot lead interruption and restoration with pickup held can restart without a STOP event.',
                               'AC voltage trip depends on working HOST firmware and a working command path. Hardware LOCAL retains OEM control.'])
    (FIELD/'checks/faults.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{trips} physical STOP/overload cases, {states} recovery states')

if __name__ == '__main__':
    main()
