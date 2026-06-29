"""Meta-tests for the structural-audit harness itself.

These prove the graph validator actually catches broken relative imports
(the class of bug that escaped during the palworld_aio restructure and
only surfaced at GUI runtime).
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from tests.dynamic_importer import import_from

graph_validator = import_from('tests.harness.graph_validator')


# Pull the check functions we test against
_check_relative_imports_resolve = graph_validator._check_relative_imports_resolve
_resolve_relative_to_path = graph_validator._resolve_relative_to_path
_relative_target_exists = graph_validator._relative_target_exists
SRC_DIR = graph_validator.SRC_DIR


class TestRelativeImportResolver:
    """Tests for the path-resolution helper."""

    def test_resolves_single_dot_same_dir(self, tmp_path: Path, monkeypatch):
        """from .sibling import X resolves to sibling.py in same dir."""
        src = tmp_path / 'src'
        pkg = src / 'mypkg'
        pkg.mkdir(parents=True)
        (src / '__init__.py').write_text('')
        (pkg / '__init__.py').write_text('')
        (pkg / 'sibling.py').write_text('x = 1')
        importer = pkg / 'main.py'
        importer.write_text('from .sibling import x')

        monkeypatch.setattr(graph_validator, 'SRC_DIR', src)
        target = _resolve_relative_to_path(importer, level=1, module='sibling')
        assert target is not None
        assert target == pkg / 'sibling'
        assert _relative_target_exists(target)

    def test_resolves_double_dot_parent_dir(self, tmp_path: Path, monkeypatch):
        """from ..other_pkg import X resolves to parent's sibling."""
        root = tmp_path / 'src'
        root.mkdir()
        (root / '__init__.py').write_text('')
        pkg_a = root / 'pkg_a'
        pkg_a.mkdir()
        (pkg_a / '__init__.py').write_text('')
        pkg_b = root / 'pkg_b'
        pkg_b.mkdir()
        (pkg_b / '__init__.py').write_text('')
        importer = pkg_a / 'main.py'
        importer.write_text('from ..pkg_b import thing')

        monkeypatch.setattr(graph_validator, 'SRC_DIR', root)
        target = _resolve_relative_to_path(importer, level=2, module='pkg_b')
        assert target is not None
        assert target == pkg_b
        assert _relative_target_exists(target)

    def test_resolves_triple_dot_grandparent(self, tmp_path: Path, monkeypatch):
        """from ...utils import X from a 2-deep subdir reaches root sibling."""
        root = tmp_path / 'src'
        root.mkdir()
        (root / '__init__.py').write_text('')
        (root / 'utils.py').write_text('x = 1')
        deep = root / 'ui' / 'chrome'
        deep.mkdir(parents=True)
        for d in (root / 'ui', deep):
            (d / '__init__.py').write_text('')
        importer = deep / 'header.py'
        importer.write_text('from ...utils import x')

        monkeypatch.setattr(graph_validator, 'SRC_DIR', root)
        target = _resolve_relative_to_path(importer, level=3, module='utils')
        assert target is not None
        assert target == root / 'utils'
        assert _relative_target_exists(target)

    def test_returns_none_outside_src_dir(self, tmp_path: Path, monkeypatch):
        """Files outside SRC_DIR can't be anchored."""
        real_src = SRC_DIR  # the actual project src/
        outside = tmp_path / 'random.py'
        outside.write_text('from .thing import x')
        # Ensure tmp_path is NOT under the real SRC_DIR (it won't be)
        result = _resolve_relative_to_path(outside, level=1, module='thing')
        assert result is None


class TestRelativeImportCheck:
    """Tests for the check function that scans files for broken imports."""

    def test_catches_broken_relative_import(self, tmp_path: Path, monkeypatch):
        """A broken 'from ..nonexistent import X' must be flagged."""
        pkg = tmp_path / 'src' / 'mypkg'
        pkg.mkdir(parents=True)
        for d in (tmp_path / 'src', pkg):
            (d / '__init__.py').write_text('')
        importer = pkg / 'main.py'
        importer.write_text(textwrap.dedent('''
            from ..nonexistent import thing

            def lazy():
                from ..also_broken import other
        '''))

        # Monkeypatch SRC_DIR so the resolver anchors correctly
        monkeypatch.setattr(graph_validator, 'SRC_DIR', tmp_path / 'src')
        monkeypatch.setattr(graph_validator, 'PROJECT_ROOT', tmp_path)

        violations = _check_relative_imports_resolve([importer])
        # Should catch BOTH the top-level and the lazy in-function import
        assert len(violations) == 2
        assert 'nonexistent' in violations[0]
        assert 'also_broken' in violations[1]

    def test_passes_valid_relative_import(self, tmp_path: Path, monkeypatch):
        """A valid 'from .sibling import X' must NOT be flagged."""
        pkg = tmp_path / 'src' / 'mypkg'
        pkg.mkdir(parents=True)
        for d in (tmp_path / 'src', pkg):
            (d / '__init__.py').write_text('')
        (pkg / 'sibling.py').write_text('thing = 1')
        importer = pkg / 'main.py'
        importer.write_text(textwrap.dedent('''
            from .sibling import thing

            def lazy():
                from .sibling import other
        '''))

        monkeypatch.setattr(graph_validator, 'SRC_DIR', tmp_path / 'src')
        monkeypatch.setattr(graph_validator, 'PROJECT_ROOT', tmp_path)

        violations = _check_relative_imports_resolve([importer])
        assert violations == []

    def test_skips_dotted_form_from_dot_import(self, tmp_path: Path, monkeypatch):
        """'from . import X' (no module) is skipped — X may be __init__ attr."""
        pkg = tmp_path / 'src' / 'mypkg'
        pkg.mkdir(parents=True)
        for d in (tmp_path / 'src', pkg):
            (d / '__init__.py').write_text('X = 1\n')
        importer = pkg / 'main.py'
        importer.write_text('from . import X\n')

        monkeypatch.setattr(graph_validator, 'SRC_DIR', tmp_path / 'src')
        monkeypatch.setattr(graph_validator, 'PROJECT_ROOT', tmp_path)

        violations = _check_relative_imports_resolve([importer])
        assert violations == []

    def test_catches_wrong_dot_depth(self, tmp_path: Path, monkeypatch):
        """from ..utils (2 dots from a 1-deep file) goes too high."""
        root = tmp_path / 'src'
        root.mkdir()
        (root / '__init__.py').write_text('')
        pkg = root / 'mypkg'
        pkg.mkdir()
        (pkg / '__init__.py').write_text('')
        # utils.py lives at root/mypkg/utils.py
        (pkg / 'utils.py').write_text('x = 1')
        importer = pkg / 'main.py'
        # Bug: should be 'from .utils' but uses '..utils' (too many dots)
        importer.write_text('from ..utils import x\n')

        monkeypatch.setattr(graph_validator, 'SRC_DIR', root)
        monkeypatch.setattr(graph_validator, 'PROJECT_ROOT', tmp_path)

        violations = _check_relative_imports_resolve([importer])
        assert len(violations) == 1
        assert '..utils' in violations[0]


class TestLiveCodebaseClean:
    """Integration: the real src/ tree must have zero broken relative imports."""

    def test_no_broken_relative_imports_in_src(self):
        """Scans every .py under src/ and verifies all relative imports resolve."""
        files = []
        for py in SRC_DIR.rglob('*.py'):
            if '__pycache__' in py.parts:
                continue
            files.append(py)

        assert files, 'Expected to find .py files under SRC_DIR'

        violations = _check_relative_imports_resolve(files)
        if violations:
            detail = '\n'.join(f'  {v}' for v in violations)
            pytest.fail(
                f'{len(violations)} broken relative import(s) found in src/:\n{detail}'
            )

    def test_full_graph_validator_passes(self):
        """The full run_graph_validator() must report 0 relative-import failures."""
        section = graph_validator.run_graph_validator()
        relative_failures = [
            f for f in section.failures if 'resolves to' in f.lower()
        ]
        if relative_failures:
            detail = '\n'.join(f'  {f}' for f in relative_failures)
            pytest.fail(
                f'graph_validator found broken relative imports:\n{detail}'
            )
