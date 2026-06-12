from __future__ import annotations

import ast
import sys
from pathlib import Path
from tests.structural_report import ReportSection


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / 'src'
TESTS_DIR = PROJECT_ROOT / 'tests'
SCRIPTS_DIR = PROJECT_ROOT / 'scripts' / 'scrs'

_STARTUP_FILES = {'bootup.py', 'loading_manager.py', 'common.py', 'path_setup.py'}
_SRC_PACKAGES = {'palworld_aio', 'palworld_toolsets', 'palworld_coord', 'palworld_xgp_import', 'i18n'}
_INSTALLED_PACKAGES = {'palsav', 'palooz'}


def _collect_py_files() -> list[Path]:
    files: list[Path] = []
    for base in (SRC_DIR, TESTS_DIR, SCRIPTS_DIR):
        if base.exists():
            for py in base.rglob('*.py'):
                if '__pycache__' in py.parts:
                    continue
                files.append(py)
    return files


def _module_name_from_path(path: Path) -> str:
    try:
        rel = path.relative_to(PROJECT_ROOT)
    except ValueError:
        return path.stem
    parts = list(rel.parts)
    if parts[-1] == '__init__.py':
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace('.py', '')
    return '.'.join(parts)


def _resolve_import(module: str, filepath: Path) -> list[str]:
    top = module.split('.')[0]
    if top in _INSTALLED_PACKAGES:
        return [top]
    if top == 'tests':
        return [module]
    if module.startswith('.'):
        return _resolve_relative_import(module, filepath)
    return [module]


def _resolve_relative_import(module: str, filepath: Path) -> list[str]:
    return [f'<relative:{filepath.name}:{module}>']


def parse_imports(path: Path) -> list[tuple[str, int, str]]:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
    except SyntaxError:
        return []

    imports: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((path.name, node.lineno or 0, alias.name))
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ''
            for alias in node.names:
                full = f'{mod}.{alias.name}' if mod else alias.name
                imports.append((path.name, node.lineno or 0, full))
    return imports


def _build_adjacency(files: list[Path]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {}
    for f in files:
        mod = _module_name_from_path(f)
        adj.setdefault(mod, set())
        for _, _, imported in parse_imports(f):
            resolved = _resolve_import(imported, f)
            for r in resolved:
                adj[mod].add(r)
    return adj


def _detect_circular(adj: dict[str, set[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: list[str] = []

    def dfs(node: str, path: list[str]) -> None:
        if node in rec_stack:
            idx = rec_stack.index(node)
            cycle = rec_stack[idx:] + [node]
            cycles.append(cycle)
            return
        if node in visited:
            return
        if node not in adj:
            return
        visited.add(node)
        rec_stack.append(node)
        for neighbor in adj[node]:
            dfs(neighbor, path + [neighbor])
        rec_stack.pop()

    for node in list(adj.keys()):
        if node not in visited:
            dfs(node, [node])

    return cycles


def _check_test_import_purity(files: list[Path]) -> list[str]:
    violations: list[str] = []
    for f in files:
        if not str(f).startswith(str(TESTS_DIR)):
            continue
        if f.name == 'conftest.py':
            continue
        if 'dynamic_importer' in f.name:
            continue
        try:
            tree = ast.parse(f.read_text(encoding='utf-8', errors='replace'))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split('.')[0]
                    if top in _SRC_PACKAGES or top == 'src':
                        violations.append(
                            f'{f.relative_to(PROJECT_ROOT)}:{node.lineno}: '
                            f'direct import "{alias.name}" — use import_from() instead'
                        )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ''
                top = mod.split('.')[0]
                if top in _SRC_PACKAGES or top == 'src':
                    names = ', '.join(a.name for a in node.names)
                    violations.append(
                        f'{f.relative_to(PROJECT_ROOT)}:{node.lineno}: '
                        f'direct import "from {mod} import {names}" — use import_from() instead'
                    )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == 'sys'
                        and node.func.attr in ('path.insert', 'path.append')
                    ):
                        violations.append(
                            f'{f.relative_to(PROJECT_ROOT)}:{node.lineno}: '
                            f'raw sys.path mutation — use conftest.py or import_from()'
                        )
    return violations


def _check_startup_files(files: list[Path]) -> list[str]:
    warnings: list[str] = []
    for f in files:
        if f.name not in _STARTUP_FILES:
            continue
        try:
            tree = ast.parse(f.read_text(encoding='utf-8', errors='replace'))
        except SyntaxError:
            continue
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Expr, ast.Assign, ast.If, ast.Call)):
                if isinstance(node, ast.If):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                            if isinstance(child.func.value, ast.Name) and child.func.value.id in (
                                'QApplication', 'QDialog', 'QMainWindow'
                            ):
                                warnings.append(
                                    f'{f.relative_to(PROJECT_ROOT)}:{node.lineno}: '
                                    f'module-level conditional triggers Qt UI code during import'
                                )
                                break
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in (
                        'resource_path', 'init_language', 'QApplication'
                    ):
                        warnings.append(
                            f'{f.relative_to(PROJECT_ROOT)}:{node.lineno}: '
                            f'module-level call to "{node.func.id}" — may execute during import'
                        )
                    elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                        if node.func.value.id == 'sys' and node.func.attr in ('path.insert', 'path.append'):
                            warnings.append(
                                f'{f.relative_to(PROJECT_ROOT)}:{node.lineno}: '
                                f'module-level sys.path mutation — side effect on import'
                            )
    return warnings


def run_graph_validator() -> ReportSection:
    section = ReportSection('Import Graph')
    files = _collect_py_files()

    adj = _build_adjacency(files)
    cycles = _detect_circular(adj)

    if cycles:
        deduped = []
        seen = set()
        for c in cycles:
            key = str(sorted(c))
            if key not in seen:
                seen.add(key)
                deduped.append(c)
        section.failures.append(f'{len(deduped)} circular import chain(s) detected:')
        for cycle in deduped:
            arrow = ' -> '.join(cycle)
            section.failures.append(f'  {arrow}')

    purity_violations = _check_test_import_purity(files)
    if purity_violations:
        section.failures.append(
            f'{len(purity_violations)} test import purity violation(s):'
        )
        for v in purity_violations:
            section.failures.append(f'  {v}')

    startup_warnings = _check_startup_files(files)
    if startup_warnings:
        section.warnings.append(
            f'{len(startup_warnings)} startup module-level execution warning(s):'
        )
        for w in startup_warnings:
            section.warnings.append(f'  {w}')

    module_count = len(adj)
    d = f'{module_count} modules scanned, {len(cycles)} cycle(s), {len(purity_violations)} purity violation(s)'
    if startup_warnings:
        d += f', {len(startup_warnings)} startup warning(s)'
    if cycles or purity_violations:
        section.failures.insert(0, d)
    else:
        section.warnings.insert(0, d)
    return section
