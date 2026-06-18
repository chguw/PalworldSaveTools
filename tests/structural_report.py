from __future__ import annotations

import sys


class StructuralReport:
    def __init__(self):
        self.sections: list[ReportSection] = []

    def add_section(self, section: ReportSection) -> None:
        self.sections.append(section)

    def has_errors(self) -> bool:
        return any(s.failures for s in self.sections)

    @property
    def all_failures(self) -> list[str]:
        return [f for s in self.sections for f in s.failures]

    @property
    def all_warnings(self) -> list[str]:
        return [w for s in self.sections for w in s.warnings]

    def format(self, verbose: bool = False) -> str:
        lines = ['=' * 72, 'STRUCTURAL INTEGRITY REPORT', '=' * 72]
        for s in self.sections:
            lines.append(f'\n--- {s.name} ---')
            if s.failures:
                lines.append(f'  FAILURES ({len(s.failures)}):')
                for f in s.failures:
                    if verbose:
                        lines.append(f'    [FAIL] {f}')
                    else:
                        prefix = f'    [FAIL] {f[:160]}'
                        lines.append(prefix + ('...' if len(f) > 160 else ''))
            if s.warnings:
                lines.append(f'  WARNINGS ({len(s.warnings)}):')
                for w in s.warnings:
                    lines.append(f'    [WARN] {w}')
            if not s.failures and not s.warnings:
                lines.append('  All checks passed.')
        if self.has_errors():
            lines.append(f'\n{"=" * 72}')
            lines.append(f'{len(self.all_failures)} failure(s), {len(self.all_warnings)} warning(s)')
            lines.append('=' * 72)
        return '\n'.join(lines)

    def exit_if_errors(self) -> None:
        if self.has_errors():
            print(self.format(verbose=True), file=sys.stderr)
            raise SystemExit(1)


class ReportSection:
    def __init__(self, name: str):
        self.name = name
        self.failures: list[str] = []
        self.warnings: list[str] = []
