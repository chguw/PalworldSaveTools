#!/usr/bin/env python3
"""
Windows build → Inno Setup portable installer, all in one command.

Builds a Nuitka onedir (standalone) directory, then compiles a minimal
Inno Setup script into a single portable .exe installer.  Inno Setup
produces proper Windows PE executables that do not trigger heuristic
false-positive flags from Windows Defender or VirusTotal.

Usage:
    uv run python build/windows_build.py
"""

import os
import sys
import shutil
import subprocess
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, '..'))
os.chdir(ROOT_DIR)

DIST_DIR = os.path.join(ROOT_DIR, 'dist')
ISS_TEMPLATE = os.path.join(ROOT_DIR, 'build', 'Portable.iss')


# ── helpers ──────────────────────────────────────────────────────────────

def get_app_version() -> str:
    common_file = os.path.join('src', 'common.py')
    if not os.path.exists(common_file):
        return 'unknown'
    with open(common_file, 'r') as f:
        for line in f:
            if line.strip().startswith('APP_VERSION'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return 'unknown'


def get_app_name() -> str:
    common_file = os.path.join('src', 'common.py')
    if not os.path.exists(common_file):
        return 'PalworldSaveTools'
    with open(common_file, 'r') as f:
        for line in f:
            if line.strip().startswith('APP_NAME'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return 'PalworldSaveTools'


def run(cmd: list, desc: str = ''):
    if desc:
        print(f'-- {desc} --')
    print(f'$ {" ".join(cmd)}')
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f'ERROR: step failed with exit code {result.returncode}')
        sys.exit(result.returncode)
    return result


# ── steps ────────────────────────────────────────────────────────────────

def build_nuitka_onedir():
    """Run the existing Nuitka build script in --onedir mode."""
    run(['uv', 'run', 'python', 'build/nuitka/build_nuitka.py', '--onedir'],
        'Building with Nuitka (onedir)')


def find_dist_dir(app_name: str, version: str) -> str:
    """Locate the Nuitka onedir dist directory in dist/."""
    candidate = os.path.join(DIST_DIR, f'{app_name}-V{version}-win.exe.dist')
    if os.path.isdir(candidate):
        return candidate
    # Fallback: any .dist dir matching the naming pattern
    import glob
    matches = sorted(glob.glob(os.path.join(DIST_DIR, f'{app_name}-V*-win.exe.dist')))
    if not matches:
        print(f'ERROR: No onedir dist directory found matching '
              f'{app_name}-V*-win.exe.dist')
        print(f'Contents of dist/: {os.listdir(DIST_DIR)}')
        sys.exit(1)
    return matches[0]


def compile_installer(app_name: str, version: str, dist_dir: str):
    """Compile the Inno Setup Portable.iss into the final installer .exe.

    Passes version-specific values via /D defines so the .iss template
    stays reusable across builds.
    """
    exe_name = f'{app_name}-V{version}-win.exe'
    dir_name = os.path.basename(dist_dir)

    if not os.path.exists(ISS_TEMPLATE):
        print(f'ERROR: Inno Setup script not found at {ISS_TEMPLATE}')
        sys.exit(1)

    cmd = [
        'iscc',
        f'/DAppVersion={version}',
        f'/DAppExeName={exe_name}',
        f'/DAppDirName={dir_name}',
        ISS_TEMPLATE,
    ]
    run(cmd, 'Compiling Inno Setup installer')

    # iscc outputs to dist/{app_name}-V{version}-win.exe per OutputBaseFilename
    out_path = os.path.join(DIST_DIR, exe_name)
    if not os.path.exists(out_path):
        print(f'ERROR: iscc completed but output not found at {out_path}')
        print(f'Contents of dist/: {os.listdir(DIST_DIR)}')
        sys.exit(1)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f'Installer created: {out_path} ({size_mb:.1f} MB)')
    return out_path


# ── main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Windows build + Inno Setup portable installer (one command)'
    )
    parser.parse_args()

    version = get_app_version()
    app_name = get_app_name()
    print(f'Building {app_name} v{version} for Windows (onedir + Inno Setup)')

    # Step 1: Nuitka build --onedir
    build_nuitka_onedir()

    # Step 2: Locate the onedir
    dist_dir = find_dist_dir(app_name, version)
    print(f'Found onedir: {dist_dir}')

    # Step 3: Compile Inno Setup installer from the onedir
    out_path = compile_installer(app_name, version, dist_dir)

    # Step 4: Remove the raw onedir — installer is the sole Windows artifact
    if os.path.isdir(dist_dir):
        shutil.rmtree(dist_dir, ignore_errors=True)
        print(f'Removed raw onedir ({os.path.basename(dist_dir)})')

    print(f'\n✓ Windows build complete: {out_path}')


if __name__ == '__main__':
    main()
