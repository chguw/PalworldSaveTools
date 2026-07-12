#!/usr/bin/env python3
"""
Windows build → 7-Zip SFX portable executable, all in one command.

Builds a Nuitka onedir (standalone) directory, then wraps it into a single
self-extracting .exe using 7-Zip's SFX module.  The SFX stub (7zSD.sfx) is
signed by the 7-Zip author (Igor Pavlov) and is well-known to antivirus
engines, avoiding the false-positive heuristic flags that Nuitka's --onefile
often triggers.

The resulting .exe works identically to the old onefile — users double-click
and the app runs — but internally it self-extracts to %TEMP% and launches
the real binary.  No installation required.

Usage:
    uv run python build/windows_build.py            # build + SFX package
"""

import os
import sys
import shutil
import subprocess
import zipfile
import argparse
from urllib.request import urlopen

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, '..'))
os.chdir(ROOT_DIR)

DIST_DIR = os.path.join(ROOT_DIR, 'dist')

# 7-Zip Extra package — provides 7zSD.sfx (GUI self-extracting module).
# URL uses a pinned 7-Zip release; bump this when updating 7-Zip.
SFX_PACKAGE_URL = 'https://www.7-zip.org/a/7z2405-extra.7z'


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
    candidate = os.path.join(DIST_DIR, f'{app_name}-V{version}-win.dist')
    if os.path.isdir(candidate):
        return candidate
    # Fallback: any .dist dir matching the pattern
    import glob
    matches = sorted(glob.glob(os.path.join(DIST_DIR, f'{app_name}-V*-win.dist')))
    if not matches:
        print(f'ERROR: No onedir dist directory found matching '
              f'{app_name}-V*-win.dist')
        print(f'Contents of dist/: {os.listdir(DIST_DIR)}')
        sys.exit(1)
    return matches[0]


def ensure_sfx_module() -> str:
    """Download 7z-extra and extract 7zSD.sfx. Returns path to the module."""
    cache_dir = os.path.join(DIST_DIR, '.cache', '7z_sfx')
    sfx_path = os.path.join(cache_dir, '7zSD.sfx')
    if os.path.exists(sfx_path):
        return sfx_path

    os.makedirs(cache_dir, exist_ok=True)
    pkg_path = os.path.join(cache_dir, 'extra.7z')

    # Download the extra package
    if not os.path.exists(pkg_path):
        print('Downloading 7-Zip extra package (for 7zSD.sfx)...')
        try:
            with urlopen(SFX_PACKAGE_URL) as resp:
                with open(pkg_path, 'wb') as f:
                    f.write(resp.read())
            print(f'Downloaded → {pkg_path}')
        except Exception as e:
            print(f'ERROR: failed to download SFX package: {e}')
            sys.exit(1)

    # Extract 7zSD.sfx from the package
    print(f'Extracting 7zSD.sfx from {pkg_path}...')
    # The extra.7z contains a single directory 'extra/' with the modules inside.
    # 7zSD.sfx is inside the archive at extra/7zSD.sfx (or 7zSD.sfx).
    # We'll use Python's zipfile or just try 7z extraction.
    # 7z cannot extract its own .7z format without being installed, but we
    # know 7z.exe is available (installed via choco in the workflow).
    run(['7z', 'x', pkg_path, '-o' + cache_dir, '-y', '7zSD.sfx'],
        'Extracting 7zSD.sfx')
    # The archive may contain a subdirectory 'extra/' — if so the file
    # landed at cache_dir/extra/7zSD.sfx.  Move it up.
    extra_sub = os.path.join(cache_dir, 'extra')
    if os.path.isdir(extra_sub):
        src = os.path.join(extra_sub, '7zSD.sfx')
        if os.path.exists(src):
            shutil.move(src, sfx_path)
            shutil.rmtree(extra_sub, ignore_errors=True)

    if not os.path.exists(sfx_path):
        print(f'ERROR: 7zSD.sfx not found after extraction (looked at {sfx_path})')
        sys.exit(1)
    return sfx_path


def package_sfx(app_dir: str, app_name: str, version: str,
                sfx_module: str) -> str:
    """Create a 7-Zip SFX from the onedir directory.

    Structure:
        copy /b 7zSD.sfx + config.txt + archive.7z = output.exe
    """
    out_name = f'{app_name}-V{version}-win.exe'
    out_path = os.path.join(DIST_DIR, out_name)

    # The main binary inside the onedir is named by Nuitka's --output-filename.
    # For  --onedir  the binary name follows the same pattern:
    binary_name = f'{app_name}-V{version}-win.exe'
    binary_path = os.path.join(app_dir, binary_name)
    if not os.path.exists(binary_path):
        print(f'ERROR: expected binary not found at {binary_path}')
        sys.exit(1)

    # ── Create config.txt ────────────────────────────────────────────────
    config_lines = [
        ';!@Install@!UTF-8!',
        f'Title="{app_name} v{version}"',
        'BeginPrompt="Extracting Palworld Save Tools..."',
        f'RunProgram="{binary_name}"',
        f'Directory="%TEMP%\\\\{app_name}"',
        ';!@InstallEnd@!',
    ]
    config_path = os.path.join(DIST_DIR, 'sfx_config.txt')
    with open(config_path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write('\r\n'.join(config_lines) + '\r\n')

    # ── Create 7z archive of the onedir contents ─────────────────────────
    archive_path = os.path.join(DIST_DIR, 'archive.7z')
    if os.path.exists(archive_path):
        os.remove(archive_path)
    # 7z requires trailing slash on the source dir to archive its contents
    # rather than the dir itself.
    source = app_dir + ('' if app_dir.endswith('\\') else os.sep)
    run(['7z', 'a', '-mx9', '-y', archive_path, source + '*'],
        'Creating 7z archive')

    # ── Concatenate SFX stub + config + archive ──────────────────────────
    if os.path.exists(out_path):
        os.remove(out_path)
    print(f'Assembling SFX → {out_name}')
    with open(out_path, 'wb') as out:
        for src in (sfx_module, config_path, archive_path):
            with open(src, 'rb') as f:
                shutil.copyfileobj(f, out)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f'SFX created: {out_path} ({size_mb:.1f} MB)')

    # Clean up intermediates
    for p in (config_path, archive_path):
        try:
            os.remove(p)
        except OSError:
            pass

    return out_path


# ── main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Windows build + 7-Zip SFX packaging (one command)'
    )
    # For future flags — currently no extra options needed
    parser.parse_args()

    version = get_app_version()
    app_name = get_app_name()
    print(f'Building {app_name} v{version} for Windows (onedir + 7z SFX)')

    # Step 1: Nuitka build → onedir
    build_nuitka_onedir()

    # Step 2: Locate the onedir
    dist_dir = find_dist_dir(app_name, version)
    print(f'Found onedir: {dist_dir}')

    # Step 3: Ensure the SFX module is available
    sfx_module = ensure_sfx_module()
    print(f'SFX module: {sfx_module}')

    # Step 4: Package into SFX
    sfx_path = package_sfx(dist_dir, app_name, version, sfx_module)

    # Step 5: Remove the raw onedir — SFX is the sole Windows artifact
    if os.path.isdir(dist_dir):
        shutil.rmtree(dist_dir, ignore_errors=True)
        print(f'Removed raw onedir ({os.path.basename(dist_dir)}) — '
              f'SFX is the sole Windows artifact')

    print(f'\n✓ Windows build complete: {sfx_path}')


if __name__ == '__main__':
    main()
