from __future__ import annotations
import os, sys, subprocess, shutil, pathlib, argparse, threading, webbrowser
PROJECT_DIR = pathlib.Path(__file__).resolve().parent
uv_lock = PROJECT_DIR / 'uv.lock'
if uv_lock.exists():
    uv_lock.unlink()
VENV_DIR = PROJECT_DIR / '.venv'
USE_ANSI = True
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass
def ansi(code: str) -> str:
    return code if USE_ANSI else ''
RESET = ansi('\x1b[0m')
BOLD = ansi('\x1b[1m')
GREEN = ansi('\x1b[32m')
YELLOW = ansi('\x1b[33m')
RED = ansi('\x1b[31m')
CYAN = ansi('\x1b[36m')
DIM = ansi('\x1b[2m')
LOGO = "\n  ___      _                _    _ ___              _____         _    \n | _ \\__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___\n |  _/ _` | \\ V  V / _ \\ '_| / _` \\__ \\/ _` \\ V / -_)| |/ _ \\/ _ \\(_-<\n |_| \\__,_|_|\\_/\\_/\\___/_| |_\\__,_|___/\\__,_|\\_/\\___||_|\\___/\\___/_/__/\n"
def log(msg: str, color: str=''):
    print(f'{color}{msg}{RESET}')
def venv_python() -> pathlib.Path:
    if os.name == 'nt':
        return VENV_DIR / 'Scripts' / 'python.exe'
    return VENV_DIR / 'bin' / 'python'
def ensure_venv():
    vpy = venv_python()
    if vpy.exists():
        return True
    log('Creating virtual environment...', CYAN)
    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR, ignore_errors=True)
    result = subprocess.run(['uv', 'venv', str(VENV_DIR)])
    if result.returncode != 0:
        log('Failed to create venv', RED)
        return False
    log('Installing dependencies...', CYAN)
    result = subprocess.run(['uv', 'sync'])
    uv_lock = PROJECT_DIR / 'uv.lock'
    if uv_lock.exists():
        uv_lock.unlink()
    if result.returncode == 0:
        log('Environment ready', GREEN)
        return True
    else:
        log('Failed to install dependencies', RED)
        if VENV_DIR.exists():
            shutil.rmtree(VENV_DIR, ignore_errors=True)
        return False
def main():
    parser = argparse.ArgumentParser(description='PalworldSaveTools')
    parser.add_argument('--web', action='store_true', help='Launch WebUI instead of desktop GUI')
    args = parser.parse_args()

    print(f'{BOLD}{LOGO}{RESET}')
    if not ensure_venv():
        log('Setup failed', RED)
        input('Press Enter to exit...')
        sys.exit(1)

    vpy = venv_python()
    if args.web:
        frontend_dir = PROJECT_DIR / 'web' / 'frontend'
        backend_py = PROJECT_DIR / 'web' / 'backend' / 'main.py'

        _shell = os.name == 'nt'

        # Check for node_modules — install if missing
        nm = frontend_dir / 'node_modules'
        if not nm.exists() or not any(nm.iterdir()):
            log('Installing frontend dependencies...', CYAN)
            r = subprocess.run(['npm', 'install'], cwd=str(frontend_dir), shell=_shell)
            if r.returncode != 0:
                log('Failed to install frontend dependencies', RED)
                sys.exit(1)

        # Start frontend dev server
        frontend_proc = subprocess.Popen(
            ['npm', 'run', 'dev', '--', '--host', '127.0.0.1', '--port', '16920'],
            cwd=str(frontend_dir), shell=_shell,
            env={**os.environ, 'PST_BACKEND_URL': 'http://127.0.0.1:16921'},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
        )

        frontend_ready = threading.Event()

        def log_frontend():
            try:
                for line in iter(frontend_proc.stdout.readline, ''):
                    stripped = line.rstrip()
                    if stripped:
                        print(f'{DIM}[frontend] {stripped}{RESET}')
                    if 'Local:' in stripped and '16920' in stripped:
                        frontend_ready.set()
            except Exception:
                pass
        t = threading.Thread(target=log_frontend, daemon=True)
        t.start()

        # Start backend
        log('Starting PST WebUI backend...', GREEN)
        backend_proc = subprocess.Popen(
            [str(vpy), str(backend_py)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
        )

        def log_backend():
            try:
                for line in iter(backend_proc.stdout.readline, ''):
                    stripped = line.rstrip()
                    if stripped:
                        print(f'{DIM}[backend] {stripped}{RESET}')
            except Exception:
                pass
        t2 = threading.Thread(target=log_backend, daemon=True)
        t2.start()

        log(f'  Frontend → http://127.0.0.1:16920', GREEN)
        log(f'  Backend  → http://127.0.0.1:16921', GREEN)
        log(f'  Press Ctrl+C to stop', DIM)

        if frontend_ready.wait(timeout=60):
            webbrowser.open('http://127.0.0.1:16920')

        def cleanup():
            for p in (frontend_proc, backend_proc):
                if p.poll() is None:
                    try:
                        p.terminate()
                        p.wait(timeout=3)
                    except Exception:
                        try:
                            p.kill()
                        except Exception:
                            pass
        try:
            frontend_proc.wait()
            backend_proc.terminate()
            backend_proc.wait()
        except KeyboardInterrupt:
            cleanup()
            sys.exit(0)
        except Exception:
            cleanup()
            sys.exit(1)
    else:
        bootup_py = PROJECT_DIR / 'src' / 'bootup.py'
        log('Starting PalworldSaveTools...', GREEN)
        try:
            result = subprocess.run([str(vpy), str(bootup_py)])
            sys.exit(result.returncode)
        except KeyboardInterrupt:
            sys.exit(0)
if __name__ == '__main__':
    main()
