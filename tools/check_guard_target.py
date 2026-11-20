"""Build and link the guarded GPIO component in a disabled ESP32-C6 test application."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'espressif/idf:v5.4.2'
FIXTURE = Path('design/review-fixtures/guard-target')
COMPONENT = Path('firmware/components/starter_outputs')
REPORT = ROOT / 'hardware/main-compact-dual/checks/guard-target-build.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    sources = sorted(path for folder in (ROOT / FIXTURE, ROOT / COMPONENT)
                     for path in folder.rglob('*') if path.is_file() and 'tests' not in path.parts)
    before = {str(path.relative_to(ROOT)): digest(path) for path in sources}
    scratch = ROOT / 'tmp'
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as work:
        subprocess.run(['docker', 'run', '--rm', '--network', 'none', '-e', 'IDF_COMPONENT_MANAGER=0',
                        '-e', 'IDF_TARGET=esp32c6', '-v', f'{ROOT / COMPONENT}:/{COMPONENT}:ro',
                        '-v', f'{ROOT / FIXTURE}:/{FIXTURE}:ro', '-v', f'{work}:/build',
                        '-w', '/' + str(FIXTURE), IMAGE, 'idf.py', '-B', '/build',
                        '-DSDKCONFIG=/build/sdkconfig', 'build'], check=True)
        out = Path(work)
        desc = json.loads((out / 'project_description.json').read_text())
        elf = (out / desc['app_elf']).read_bytes()
        if desc['target'] != 'esp32c6' or elf[:4] != b'\x7fELF' or int.from_bytes(elf[18:20], 'little') != 243:
            raise ValueError('Expected an ESP32-C6 RISC-V ELF')
        if before != {str(path.relative_to(ROOT)): digest(path) for path in sources}:
            raise ValueError('Target build inputs changed')
        image = subprocess.check_output(['docker', 'image', 'inspect', IMAGE, '--format',
                                         '{{index .RepoDigests 0}}'], text=True).strip()
        result = dict(target=desc['target'], idf_version=desc['git_revision'], sdk_image=image,
                      fixture='Disabled ESP32-C6 configuration, links legacy guard and metered SPI/control entry points',
                      source_sha256=before, elf_machine='RISC-V', target_executed=False,
                      physical_motor_or_guard_tested=False)
        REPORT.write_text(json.dumps(result, indent=2) + '\n')
        print(REPORT.relative_to(ROOT))


if __name__ == '__main__':
    build()
