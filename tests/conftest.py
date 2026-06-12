from __future__ import annotations

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
