from __future__ import annotations

from pathlib import Path
from tests.structural_report import ReportSection


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / 'src'
TESTS_DIR = PROJECT_ROOT / 'tests'
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'

_SOURCE_ROOTS = [SRC_DIR, SCRIPTS_DIR / 'scrs']

_VENDORED_SKIP = {'palsav'}

_TEST_STEM_ALIASES: dict[str, str] = {
    'asset_paths': 'common',
    'version': 'common',
    'coords': 'palworld_coord/__init__',
    'i18n': 'i18n/__init__',
    'archive': 'palsav.archive',
    'gvas': 'palsav.gvas',
    'json_tools': 'palsav.json_tools',
    'graph_validator_relative_imports': 'graph_validator',
}

_INSTALLED_MODULES: dict[str, str] = {
    'archive': 'palsav.archive',
    'gvas': 'palsav.gvas',
    'json_tools': 'palsav.json_tools',
    'graph_validator': 'tests.harness.graph_validator',
}


def _is_vendored(path: Path) -> bool:
    try:
        rel = path.relative_to(SRC_DIR)
        if rel.parts and rel.parts[0] in _VENDORED_SKIP:
            return True
    except ValueError:
        pass
    return False


def _scan_sources() -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for root in _SOURCE_ROOTS:
        if not root.exists():
            continue
        for py_file in root.rglob('*.py'):
            if '__pycache__' in py_file.parts:
                continue
            if _is_vendored(py_file):
                continue
            stem = py_file.stem
            index.setdefault(stem, []).append(py_file)
            if py_file.name == '__init__.py':
                parent = py_file.parent
                index.setdefault(f'{parent.name}/__init__', []).append(py_file)
    return index


def _resolve_source_stem(test_stem: str) -> str:
    raw = test_stem[5:] if test_stem.startswith('test_') else test_stem
    return _TEST_STEM_ALIASES.get(raw, raw)


def _scan_tests() -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for root in [TESTS_DIR / 'unit']:
        if not root.exists():
            continue
        for py_file in root.rglob('test_*.py'):
            if '__pycache__' in py_file.parts:
                continue
            stem = py_file.stem
            if stem.startswith('test_'):
                source_stem = _resolve_source_stem(stem)
                index.setdefault(source_stem, []).append(py_file)
    return index


def run_file_pairer() -> ReportSection:
    section = ReportSection('File Pairing')

    sources = _scan_sources()
    tests = _scan_tests()

    paired: set[str] = set()
    hanging: list[Path] = []
    alias_paired: set[str] = set()

    for source_stem, test_files in tests.items():
        source = sources.get(source_stem)
        if source is None:
            base_stem = source_stem.split('/')[-1].split('.')[-1]
            source = sources.get(base_stem)

        raw_stem = source_stem.split('/')[-1].split('.')[-1]
        is_installed = raw_stem in _INSTALLED_MODULES

        if source is None and is_installed:
            paired.add(source_stem)
            alias_paired.add(source_stem)
            continue

        if source:
            paired.add(source_stem)
            if source_stem in _TEST_STEM_ALIASES.values() or source_stem in _TEST_STEM_ALIASES:
                alias_paired.add(source_stem)
        else:
            for tf in test_files:
                hanging.append(tf)

    orphan_stems = sorted(set(sources.keys()) - paired)
    orphan_files: list[Path] = []
    for stem in orphan_stems:
        for f in sources[stem]:
            orphan_files.append(f)

    if alias_paired:
        section.warnings.append(f'{len(alias_paired)} alias-based pairing(s) active')

    if hanging:
        section.failures.append(
            f'{len(hanging)} test file(s) with no matching source module:'
        )
        for f in sorted(hanging):
            try:
                rel = f.relative_to(PROJECT_ROOT)
            except ValueError:
                rel = f
            section.failures.append(f'  {rel}')

    if orphan_files:
        section.warnings.append(
            f'{len(orphan_files)} source file(s) with no matching unit test:'
        )
        for f in sorted(orphan_files):
            try:
                rel = f.relative_to(PROJECT_ROOT)
            except ValueError:
                rel = f
            section.warnings.append(f'  {rel}')

    paired_count = len(paired)
    d = f'{paired_count} paired, {len(orphan_files)} untested sources, {len(hanging)} hanging tests'
    if hanging:
        d += ' (FAILURES)'
        section.failures.insert(0, d)
    else:
        section.warnings.insert(0, d)
    return section
