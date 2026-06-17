#!/usr/bin/env python3
"""
Interactive Test Runner — PalworldSaveTools

Pick what you want to test from a simple menu. No command flags to remember.

Quick mode:
  python test_interactively.py --quick   # runs the fast test suite, no menu
  python test_interactively.py --all     # runs EVERYTHING including slow save tests

Menu mode:
  python test_interactively.py           # shows the menu
"""
from __future__ import annotations

import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VENV = PROJECT_ROOT / '.venv'

if sys.platform == 'win32':
    PYTHON = str(VENV / 'Scripts' / 'python.exe')
else:
    PYTHON = str(VENV / 'bin' / 'python3')

SRC = PROJECT_ROOT / 'src'
TESTS = PROJECT_ROOT / 'tests'
SCANNER = PROJECT_ROOT / 'scripts' / 'scrs' / 'check_theme_violations.py'
VALIDATOR = PROJECT_ROOT / 'scripts' / 'scrs' / 'validate_imports.py'
LOG_DIR = PROJECT_ROOT / 'Logs' / 'Tests_Logger'

_COLORS = (
    hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    and os.environ.get('TERM') not in ('dumb', '')
)


def _(codes: str, s: str) -> str:
    return f'{codes}{s}\033[0m' if _COLORS else s


GREEN = lambda s: _('\033[92m', s)
RED = lambda s: _('\033[91m', s)
YELLOW = lambda s: _('\033[93m', s)
BLUE = lambda s: _('\033[94m', s)
CYAN = lambda s: _('\033[96m', s)
MAGENTA = lambda s: _('\033[95m', s)
BOLD = lambda s: _('\033[1m', s)
DIM = lambda s: _('\033[2m', s)

BANNER = rf"""
   {CYAN(BOLD('PalworldSaveTools'))} — {BLUE('Interactive Test Runner')}
   {DIM('Pick an option, hit Enter. No flags needed.')}
""".strip('\n')


def _build_pytest_args(
    target: str,
    verbose: bool = True,
    stop_first: bool = False,
    show_stdout: bool = False,
    include_slow: bool = False,
) -> list[str]:
    args = [PYTHON, '-m', 'pytest', target]
    if verbose:
        args.append('-v')
    args.append('--tb=short')
    if stop_first:
        args.append('-x')
    if show_stdout:
        args.append('-s')
    if include_slow:
        args.extend(['-m', ''])
    return args


def _run(cmd: list[str], *, label: str = '', log_to_file: bool = False) -> int:
    print(f'\n  {BOLD("─" * 60)}')
    if label:
        print(f'  {BLUE(BOLD(label))}')
    print(f'  {DIM("$ " + " ".join(cmd[:8]) + (" …" if len(cmd) > 8 else ""))}')
    print(f'  {BOLD("─" * 60)}\n')

    t0 = time.time()
    if log_to_file:
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        output = result.stdout + result.stderr
        print(output, end='')
        _append_log(output, label or cmd[0])
    else:
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    elapsed = time.time() - t0

    mark = GREEN('PASS') if result.returncode == 0 else RED('FAIL')
    print(f'\n  [{mark}]  {elapsed:.1f}s  (exit code {result.returncode})\n')
    return result.returncode


def _append_log(output: str, label: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    path = LOG_DIR / f'test_run_{ts}.txt'
    with open(path, 'w') as f:
        f.write(f'--- {label} ---\n')
        f.write(output)
        if not output.endswith('\n'):
            f.write('\n')


class Runner:
    def __init__(self):
        self.verbose = True
        self.stop_first = False
        self.show_stdout = False
        self.deep_audit = True
        self.strict_paths = True
        self.warning_mode = 'full'  # full | compact | counts
        self.log_to_file = False

    def _structural_flags(self) -> list[str]:
        flags: list[str] = []
        if not self.deep_audit:
            flags.append('--no-deep-audit')
        if not self.strict_paths:
            flags.append('--no-strict-paths')
        return flags

    def _warning_flags(self) -> list[str]:
        if self.warning_mode == 'full':
            return []
        return ['--warning-mode', self.warning_mode]

    def _pytest(self, target: str, label: str, include_slow: bool = False) -> int:
        args = _build_pytest_args(target, self.verbose, self.stop_first, self.show_stdout, include_slow)
        args.extend(self._structural_flags())
        args.extend(self._warning_flags())
        return _run(args, label=label, log_to_file=self.log_to_file)

    def all_tests(self) -> int:
        return self._pytest(str(TESTS), 'Full test suite (fast)')

    def all_tests_including_slow(self) -> int:
        return self._pytest(str(TESTS), 'Full test suite (including slow save tests)', include_slow=True)

    def integration_tests(self) -> int:
        return self._pytest(str(TESTS / 'integration'), 'Integration tests (imports + save files)')

    def unit_tests(self) -> int:
        return self._pytest(str(TESTS / 'unit'), 'All unit tests')

    def core_logic(self) -> int:
        return self._pytest(
            str(TESTS / 'unit' / 'core_logic'),
            'Core utilities (common, coords, version, paths, i18n)',
        )

    def palsav_core(self) -> int:
        return self._pytest(
            str(TESTS / 'unit' / 'palsav_core'),
            'Save file engine (archive, gvas, json)',
        )

    def palworld_aio(self) -> int:
        return self._pytest(
            str(TESTS / 'unit' / 'palworld_aio_tests'),
            'App utilities (constants, utils)',
        )

    def scripts_suite(self) -> int:
        return self._pytest(
            str(TESTS / 'unit' / 'scripts'),
            'Linting / scanner tests',
        )

    def save_tests(self) -> int:
        return self._pytest(
            str(TESTS / 'integration' / 'test_palworld_save.py'),
            'Save file integration tests (slow — decompress/roundtrip)',
            include_slow=True,
        )

    def single(self, path: str, label: str) -> int:
        return self._pytest(path, label)

    def theme_scan(self, ruthless: bool = False) -> int:
        cmd = [PYTHON, str(SCANNER), '--root', str(SRC)]
        if self.verbose:
            cmd.append('-v')
        if ruthless:
            cmd.append('--ruthless')
        label = 'Theme scan (no mercy — scanning every file)' if ruthless else 'Theme scan (whitelist on)'
        return _run(cmd, label=label, log_to_file=self.log_to_file)

    def json_pairing(self, ruthless: bool = False) -> int:
        target = str(TESTS / 'integration' / 'test_game_data_json.py')
        label = 'JSON pairing (no mercy — full heuristic checks)' if ruthless else 'JSON pairing (normal — false positives skipped)'
        args = _build_pytest_args(target, self.verbose, self.stop_first, self.show_stdout)
        if ruthless:
            args.append('--ruthless')
        return _run(args, label=label, log_to_file=self.log_to_file)

    def validate_imports(self) -> int:
        return _run([PYTHON, str(VALIDATOR)], label='Check all module imports', log_to_file=self.log_to_file)

    def structural_audit_all(self) -> int:
        flags = ['--deep-audit', '--strict-paths', '--dump-structural']
        cmd = [PYTHON, '-m', 'pytest', str(TESTS), '-v', '--tb=short']
        cmd.extend(flags)
        return _run(cmd, label='Structural audit (ALL checks)', log_to_file=self.log_to_file)

    def structural_file_pairing(self) -> int:
        flags = ['--deep-audit', '--no-strict-paths', '--dump-structural']
        cmd = [PYTHON, '-m', 'pytest', str(TESTS), '-v', '--tb=short']
        cmd.extend(flags)
        return _run(cmd, label='Structural audit — file pairing', log_to_file=self.log_to_file)

    def structural_import_graph(self) -> int:
        flags = ['--deep-audit', '--no-strict-paths', '--dump-structural']
        cmd = [PYTHON, '-m', 'pytest', str(TESTS), '-v', '--tb=short']
        cmd.extend(flags)
        return _run(cmd, label='Structural audit — import graph', log_to_file=self.log_to_file)

    def structural_resource_audit(self) -> int:
        flags = ['--no-deep-audit', '--strict-paths', '--dump-structural']
        cmd = [PYTHON, '-m', 'pytest', str(TESTS), '-v', '--tb=short']
        cmd.extend(flags)
        return _run(cmd, label='Structural audit — resource paths', log_to_file=self.log_to_file)

    def menu(self) -> str:
        v = GREEN('ON') if self.verbose else RED('OFF')
        x = GREEN('ON') if self.stop_first else RED('OFF')
        s = GREEN('ON') if self.show_stdout else RED('OFF')
        da = GREEN('ON') if self.deep_audit else RED('OFF')
        sp = GREEN('ON') if self.strict_paths else RED('OFF')
        wm = {'full': GREEN('full'), 'compact': CYAN('compact'), 'counts': YELLOW('counts')}[self.warning_mode]
        lf = GREEN('ON') if self.log_to_file else RED('OFF')

        print(f'''
  {BOLD("───── Test suites ─────")}
    {CYAN("1")}   Full test suite (fast)    {DIM("(excludes save I/O)")}
    {CYAN("2")}   Full test suite (ALL)      {DIM("(includes save file tests)")}
    {CYAN("3")}   Integration tests          {DIM("(imports + save files)")}
    {CYAN("4")}   Unit tests                 {DIM("(all unit tests)")}

  {BOLD("───── By area ──────────")}
    {CYAN("5")}   Core utilities             {DIM("(common, coords, version, paths, i18n)")}
    {CYAN("6")}   Save file engine           {DIM("(archive, gvas, json)")}
    {CYAN("7")}   App utilities              {DIM("(constants, utils)")}
    {CYAN("8")}   Scanner / linting tools    {DIM("(theme violations scanner)")}
    {CYAN("9")}   Save file integration      {YELLOW("(slow)")} {DIM("(Level.sav, players, roundtrip)")}

  {BOLD("───── Single files ────")}
    {CYAN("10")}  test_imports               {DIM("integration")}
    {CYAN("11")}  test_palworld_save         {YELLOW("(slow)")} {DIM("integration")}
    {CYAN("12")}  test_common                {DIM("core")}
    {CYAN("13")}  test_version               {DIM("core")}
    {CYAN("14")}  test_coords                {DIM("core")}
    {CYAN("15")}  test_path_setup            {DIM("core")}
    {CYAN("16")}  test_i18n                  {DIM("core")}
    {CYAN("17")}  test_asset_paths           {DIM("core")}
    {CYAN("18")}  test_archive               {DIM("palsav")}
    {CYAN("19")}  test_gvas                  {DIM("palsav")}
    {CYAN("20")}  test_json_tools            {DIM("palsav")}
    {CYAN("21")}  test_constants             {DIM("app")}
    {CYAN("22")}  test_utils                 {DIM("app")}
    {CYAN("23")}  test_check_theme_violations  {DIM("scanner")}
    {CYAN("24")}  test_resource_integrity     {DIM("integration")}
    {CYAN("25")}  test_game_data_json       {DIM("game data JSON schema validation")}
    {CYAN("26")}  test_relative_imports      {DIM("import audit meta-tests")}

  {BOLD("───── Structural audit ──")}
    {CYAN("A")}   Structural audit (ALL)     {DIM("file pairing + import graph + resource audit")}
    {CYAN("P")}   File pairing only          {DIM("source ↔ test mapping check")}
    {CYAN("G")}   Import graph only          {DIM("circular deps + test purity")}
    {CYAN("R")}   Resource audit only        {DIM("AST path harvest + filesystem cross-check")}

  {BOLD("───── JSON pairing ────")}
    {CYAN("J")}   JSON pairing (normal)      {DIM("skips heuristic checks, no false positives")}
    {CYAN("K")}   JSON pairing (NO MERCY)    {DIM("full heuristic checks, flags everything")}

  {BOLD("───── Scanners ────────")}
    {CYAN("T")}   Theme scan (normal)        {DIM("whitelist on, skips theme files")}
    {CYAN("U")}   Theme scan (NO MERCY)      {DIM("whitelist OFF, scans EVERYTHING")}
    {CYAN("I")}   Validate imports           {DIM("check all modules import cleanly")}

    {BOLD("───── Settings ────────")}
    {CYAN("V")}   Verbose output             {v}
    {CYAN("X")}   Stop on first fail         {x}
    {CYAN("S")}   Show stdout                {s}
    {CYAN("D")}   Deep audit                 {da} {DIM("(file pairing + import graph)")}
    {CYAN("C")}   Strict paths               {sp} {DIM("(resource path audit)")}
    {CYAN("W")}   Warning mode               {wm} {DIM("(full / compact / counts)")}
    {CYAN("L")}   Log to file                {lf}

  {DIM("─────")}
    {CYAN("Q")}   Quit
''')
        try:
            return input(f'  {BOLD("Pick one")} [{CYAN("1")}-{CYAN("26")} {DIM("|")} {CYAN("A")}{DIM("/")}{CYAN("P")}{DIM("/")}{CYAN("G")}{DIM("/")}{CYAN("R")} {DIM("|")} {CYAN("J")}{DIM("/")}{CYAN("K")} {DIM("|")} {CYAN("T")}{DIM("/")}{CYAN("U")}{DIM("/")}{CYAN("I")} {DIM("|")} {CYAN("V")}{DIM("/")}{CYAN("X")}{DIM("/")}{CYAN("S")}{DIM("/")}{CYAN("D")}{DIM("/")}{CYAN("C")}{DIM("/")}{CYAN("W")}{DIM("/")}{CYAN("L")} {DIM("|")} {CYAN("Q")}]: ').strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return 'q'

    def run_forever(self) -> None:
        print(f'\n  {BANNER}\n')
        while True:
            choice = self.menu()
            print()

            if choice in ('q', 'quit', 'exit'):
                print(f'  {GREEN("Goodbye!")}\n')
                return

            handler = {
                '1': lambda: self.all_tests(),
                '2': lambda: self.all_tests_including_slow(),
                '3': lambda: self.integration_tests(),
                '4': lambda: self.unit_tests(),
                '5': lambda: self.core_logic(),
                '6': lambda: self.palsav_core(),
                '7': lambda: self.palworld_aio(),
                '8': lambda: self.scripts_suite(),
                '9': lambda: self.save_tests(),
                '10': lambda: self.single(str(TESTS / 'integration' / 'test_imports.py'), 'test_imports'),
                '11': lambda: self._single(str(TESTS / 'integration' / 'test_palworld_save.py'), 'test_palworld_save (slow)', include_slow=True),
                '12': lambda: self.single(str(TESTS / 'unit' / 'core_logic' / 'test_common.py'), 'test_common'),
                '13': lambda: self.single(str(TESTS / 'unit' / 'core_logic' / 'test_version.py'), 'test_version'),
                '14': lambda: self.single(str(TESTS / 'unit' / 'core_logic' / 'test_coords.py'), 'test_coords'),
                '15': lambda: self.single(str(TESTS / 'unit' / 'core_logic' / 'test_path_setup.py'), 'test_path_setup'),
                '16': lambda: self.single(str(TESTS / 'unit' / 'core_logic' / 'test_i18n.py'), 'test_i18n'),
                '17': lambda: self.single(str(TESTS / 'unit' / 'core_logic' / 'test_asset_paths.py'), 'test_asset_paths'),
                '18': lambda: self.single(str(TESTS / 'unit' / 'palsav_core' / 'test_archive.py'), 'test_archive'),
                '19': lambda: self.single(str(TESTS / 'unit' / 'palsav_core' / 'test_gvas.py'), 'test_gvas'),
                '20': lambda: self.single(str(TESTS / 'unit' / 'palsav_core' / 'test_json_tools.py'), 'test_json_tools'),
                '21': lambda: self.single(str(TESTS / 'unit' / 'palworld_aio_tests' / 'test_constants.py'), 'test_constants'),
                '22': lambda: self.single(str(TESTS / 'unit' / 'palworld_aio_tests' / 'test_utils.py'), 'test_utils'),
                '23': lambda: self.single(str(TESTS / 'unit' / 'scripts' / 'test_check_theme_violations.py'), 'test_check_theme_violations'),
                '24': lambda: self.single(str(TESTS / 'integration' / 'test_resource_integrity.py'), 'test_resource_integrity'),
                '25': lambda: self.single(str(TESTS / 'integration' / 'test_game_data_json.py'), 'test_game_data_json'),
                '26': lambda: self.single(str(TESTS / 'unit' / 'harness' / 'test_graph_validator_relative_imports.py'), 'test_relative_imports'),
                'a': lambda: self.structural_audit_all(),
                'p': lambda: self.structural_file_pairing(),
                'g': lambda: self.structural_import_graph(),
                'r': lambda: self.structural_resource_audit(),
                'j': lambda: self.json_pairing(ruthless=False),
                'k': lambda: self.json_pairing(ruthless=True),
                't': lambda: self.theme_scan(ruthless=False),
                'u': lambda: self.theme_scan(ruthless=True),
                'i': lambda: self.validate_imports(),
                'v': lambda: self._toggle('verbose'),
                'x': lambda: self._toggle('stop_first'),
                's': lambda: self._toggle('show_stdout'),
                'd': lambda: self._toggle('deep_audit'),
                'c': lambda: self._toggle('strict_paths'),
                'w': lambda: self._cycle_warning_mode(),
                'l': lambda: self._toggle('log_to_file'),
            }.get(choice)

            if handler:
                handler()
            else:
                print(f'  {RED(f"Unknown: {choice!r}")}  Type a number, letter, or Q')

            print()

    def _single(self, path: str, label: str, include_slow: bool = False) -> int:
        return self._pytest(path, label, include_slow=include_slow)

    def _toggle(self, attr: str) -> None:
        current = getattr(self, attr)
        setattr(self, attr, not current)
        label = {
            'verbose': 'Verbose output',
            'stop_first': 'Stop on first fail',
            'show_stdout': 'Show stdout',
            'log_to_file': 'Log to file',
        }.get(attr, attr)
        status = GREEN('ON') if not current else RED('OFF')
        print(f'  {label}: toggled {status}')

    def _cycle_warning_mode(self) -> None:
        order = ['full', 'compact', 'counts']
        idx = order.index(self.warning_mode)
        self.warning_mode = order[(idx + 1) % len(order)]
        labels = {'full': 'full (all details)', 'compact': 'compact (summarized)', 'counts': 'counts only'}
        print(f'  Warning mode: {CYAN(labels[self.warning_mode])}')


def main() -> int:
    if '--all' in sys.argv:
        runner = Runner()
        return runner.all_tests_including_slow()
    if '--quick' in sys.argv:
        runner = Runner()
        return runner.all_tests()
    runner = Runner()
    runner.run_forever()
    return 0


if __name__ == '__main__':
    sys.exit(main())
