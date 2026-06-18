from __future__ import annotations

import os
import re
from collections import Counter

import pytest
from pathlib import Path

from tests.test_registry import PROJECT_ROOT, get_all_parent_dirs, find_source_for_test
from tests.structural_report import StructuralReport
from tests.harness.file_pairer import run_file_pairer
from tests.harness.graph_validator import run_graph_validator
from tests.harness.resource_auditor import run_resource_auditor


def pytest_addoption(parser):
    parser.addoption(
        '--skip-structural',
        action='store_true',
        default=False,
        help='Skip all structural integrity checks (file pairing, graph, resource audit)',
    )
    parser.addoption(
        '--deep-audit',
        action='store_true',
        default=True,
        dest='deep_audit',
        help='Run file pairing and import graph validation (default: on)',
    )
    parser.addoption(
        '--no-deep-audit',
        action='store_false',
        dest='deep_audit',
        help='Skip file pairing and import graph validation',
    )
    parser.addoption(
        '--strict-paths',
        action='store_true',
        default=True,
        dest='strict_paths',
        help='Run deep AST resource path audit (default: on)',
    )
    parser.addoption(
        '--no-strict-paths',
        action='store_false',
        dest='strict_paths',
        help='Skip deep AST resource path audit',
    )
    parser.addoption(
        '--dump-structural',
        action='store_true',
        default=False,
        help='Print full structural report without aborting',
    )
    parser.addoption(
        '--ruthless',
        action='store_true',
        default=False,
        help='No mercy mode — scan everything, flag potential false positives (e.g. '
             'icon-asset correlations, heuristic checks)',
    )
    parser.addoption(
        '--warning-mode',
        action='store',
        default='full',
        choices=['full', 'compact', 'counts'],
        help='Warning display mode: full (default), compact (summarized per test), counts (numbers only)',
    )


def _run_structural_audit(config) -> StructuralReport | None:
    if config.getoption('--skip-structural'):
        return None

    report = StructuralReport()

    if config.getoption('--deep-audit'):
        report.add_section(run_file_pairer())
        report.add_section(run_graph_validator())

    if config.getoption('--strict-paths'):
        report.add_section(run_resource_auditor())

    return report


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    try:
        import palsav
        if getattr(palsav, '__file__', None) is not None:
            pass
    except Exception:
        pass

    # Propagate --ruthless to test_game_data_json via env var
    if session.config.getoption('--ruthless', default=False):
        os.environ.setdefault('PST_RUTHLESS', '1')

    for parent_dir in get_all_parent_dirs():
        parent_str = str(parent_dir)
        import sys
        if parent_str not in sys.path:
            sys.path.insert(0, parent_str)

    report = _run_structural_audit(session.config)
    if report is None:
        return

    if session.config.getoption('--dump-structural'):
        print('\n' + report.format(verbose=True))
    else:
        report.exit_if_errors()


@pytest.fixture
def project_dir() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def src_dir() -> Path:
    return PROJECT_ROOT / 'src'


@pytest.fixture
def sample_sav_path(tmp_path) -> Path:
    path = tmp_path / "test_level.sav"
    path.write_bytes(b"")
    return path


@pytest.fixture
def mock_gvas_data() -> dict:
    return {
        "save_game_data": {
            "value": {
                "GroupSaveDataMap": {"value": []},
                "CharacterSaveParameterMap": {"value": []},
                "MapObjectSaveData": {"value": []},
            }
        }
    }


@pytest.fixture
def resolve_source_target(request):
    test_stem = Path(request.fspath).stem
    return find_source_for_test(test_stem)


class Helpers:
    @staticmethod
    def make_sav_path(tmp_path: Path, name: str = "Level.sav") -> Path:
        p = tmp_path / name
        p.write_bytes(b"")
        return p


@pytest.fixture
def helpers() -> Helpers:
    return Helpers()


# ---------------------------------------------------------------------------
# Warning display modes (compact / counts)
# ---------------------------------------------------------------------------

_WARNING_PREFIX_RE = re.compile(r'^.*?:\d+: \w+: ')


def _raw_msg(record):
    """Get the raw warning text from a WarningReport, stripping pytest's
    'file:line: category:' display prefix."""
    formatted = str(record.message)
    m = _WARNING_PREFIX_RE.match(formatted)
    if m:
        return formatted[m.end():]
    return formatted


def _parse_warning(record):
    """Extract (count, entity, description) from a WarningReport whose
    raw message follows '<N> <entity>(s) with <description>:\\n  ...'.
    Returns a dict or None if parsing fails.
    """
    msg = _raw_msg(record)
    first, *_ = msg.split('\n', 1)
    m = re.match(r'^(\d+)\s+(.+?)\s+(with\s+.+)', first)
    if not m:
        return None
    return {
        'count': int(m.group(1)),
        'entity': m.group(2).strip().rstrip('(s'),
        'description': m.group(3).rstrip(':').strip(),
    }


def _first_example(record):
    """Return a short (≤70 chars) example from the warning body."""
    msg = _raw_msg(record)
    for line in msg.split('\n')[1:]:
        stripped = line.strip()
        if stripped and not stripped.startswith('...'):
            return stripped[:70]
    return ''


@pytest.hookimpl(tryfirst=True)
def pytest_terminal_summary(terminalreporter, config):
    """Override default warning summary when --warning-mode is compact/counts."""
    mode = config.getoption('--warning-mode')
    if mode == 'full':
        return

    records = terminalreporter.stats.pop('warnings', [])
    if not records:
        return

    terminalreporter.write_sep('=', '')
    tw = terminalreporter

    if mode == 'counts':
        per_test = Counter()
        for r in records:
            test_name = r.nodeid.split('::')[-1]
            per_test[test_name] += 1
        tw.write_line('Warnings (counts):')
        for name, n in per_test.most_common():
            tw.write_line(f'  {name:<50s} {n:>4d}')
        tw.write_line(f'  {"─" * 55}')
        tw.write_line(f'  {"Total":<50s} {sum(per_test.values()):>4d}')
    else:  # compact
        tw.write_line('Warnings (compact):')
        for r in records:
            parsed = _parse_warning(r)
            if parsed:
                example = _first_example(r)
                ex_suffix = f'  e.g. {example}' if example else ''
                tw.write_line(
                    f'  {parsed["count"]:>5d} {parsed["entity"]:<30s}'
                    f' {parsed["description"]:<50s}{ex_suffix}'
                )
            else:
                tw.write_line(f'  {str(r.message)[:120]}')
