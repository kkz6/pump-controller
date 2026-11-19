"""Exercise guarded control components on the host and hash the inputs of the run."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / 'firmware/components'
STARTER = COMPONENTS / 'starter_outputs'
OUTPUT = ROOT / 'hardware/main-compact-dual/checks/guard-firmware.json'


def run():
    inputs = sorted(path for path in COMPONENTS.rglob('*')
                    if path.is_file() and path.suffix in ('.c', '.h', '.sh', '.txt'))
    inputs.append(ROOT / 'design/review-fixtures/pulse-stop-bus-loss.c')
    inputs.append(ROOT / 'design/review-fixtures/r2-stop-feedback.c')
    def hashes():
        return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}

    frozen = hashes()
    result = subprocess.run([STARTER / 'tests/run-host.sh'], cwd=ROOT, capture_output=True,
                            text=True, check=True)
    with tempfile.TemporaryDirectory() as tmp:
        program = Path(tmp) / 'panel-control'
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                        '-I', STARTER / 'include', STARTER / 'starter_outputs.c', STARTER / 'panel_controls.c',
                        STARTER / 'tests/panel_controls_test.c', '-o', program], check=True)
        subprocess.run([program], check=True)
    if frozen != hashes():
        raise RuntimeError('Firmware source changed during tests')
    report = dict(host_tests=result.stdout.splitlines(), panel_controls_asan_ubsan='passed',
                  source_sha256=frozen, gpio_driver='host mock', target_flashed=False,
                  physical_motor_or_guard_tested=False)
    OUTPUT.write_text(json.dumps(report, indent=2) + '\n')
    print(result.stdout, end='')


if __name__ == '__main__':
    run()
