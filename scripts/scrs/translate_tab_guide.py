import re
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print('Installing deep-translator...')
    import subprocess
    subprocess.check_call(['uv', 'pip', 'install', 'deep-translator'])
    from deep_translator import GoogleTranslator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TAB_GUIDE_SRC = PROJECT_ROOT / 'resources' / 'tab_guide' / 'en'
TAB_GUIDE_DIR = PROJECT_ROOT / 'resources' / 'tab_guide'

LANGUAGES = {
    'zh_CN': {'dir': 'zh', 'code': 'zh-CN', 'name': 'Simplified Chinese'},
    'de_DE': {'dir': 'de', 'code': 'de', 'name': 'German'},
    'es_ES': {'dir': 'es', 'code': 'es', 'name': 'Spanish'},
    'fr_FR': {'dir': 'fr', 'code': 'fr', 'name': 'French'},
    'ru_RU': {'dir': 'ru', 'code': 'ru', 'name': 'Russian'},
    'ja_JP': {'dir': 'ja', 'code': 'ja', 'name': 'Japanese'},
    'ko_KR': {'dir': 'ko', 'code': 'ko', 'name': 'Korean'},
}

HTML_TAG_PATTERN = re.compile(r'<[^>]+>')


class PlaceholderManager:
    def __init__(self):
        self.placeholders: Dict[str, str] = {}
        self.counter = 0

    def add(self, text: str, prefix: str = 'T') -> str:
        key = f'__{prefix}{self.counter}__'
        self.placeholders[key] = text
        self.counter += 1
        return key

    def restore(self, text: str) -> str:
        for key, value in sorted(self.placeholders.items(), key=lambda x: -len(x[0])):
            text = text.replace(key, value)
        return text

    def clear(self):
        self.placeholders = {}
        self.counter = 0


def protect_html_tags(text: str, pm: PlaceholderManager) -> str:
    def replace_tag(match):
        return pm.add(match.group(0), 'H')
    return HTML_TAG_PATTERN.sub(replace_tag, text)


def split_text_for_translation(text: str, max_length: int = 4500) -> List[str]:
    if len(text) <= max_length:
        return [text]
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_length = 0
    for line in lines:
        line_length = len(line) + 1
        if current_length + line_length > max_length and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(line)
        current_length += line_length
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    return chunks


def translate_text(text: str, target_lang: str, source_lang: str = 'en') -> str:
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        chunks = split_text_for_translation(text)
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                if i > 0:
                    time.sleep(0.5)
                translated = translator.translate(chunk)
                translated_chunks.append(translated)
            else:
                translated_chunks.append(chunk)
        return '\n'.join(translated_chunks)
    except Exception as e:
        print(f'Translation error: {e}')
        return text


_print_lock = threading.Lock()


def safe_print(*args, **kwargs):
    with _print_lock:
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            for arg in args:
                try:
                    print(str(arg).encode('utf-8', errors='ignore').decode('utf-8'), **kwargs)
                except:
                    print('[Unicode Error]', **kwargs)


def translate_html_file(filename: str, target_dir: str, google_code: str, lang_name: str, quiet: bool = False) -> Tuple[str, str, bool, str]:
    if not quiet:
        safe_print(f"\n{'=' * 50}")
        safe_print(f'  {filename} -> {target_dir}/ ({lang_name})')
        safe_print(f"{'=' * 50}")

    src_path = TAB_GUIDE_SRC / filename
    if not src_path.exists():
        safe_print(f'  Source not found: {src_path}')
        return (filename, target_dir, False, 'Source not found')

    with open(src_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pm = PlaceholderManager()
    protected = protect_html_tags(content, pm)

    if not quiet:
        safe_print(f'  Protected {len(pm.placeholders)} HTML tags')

    translated = translate_text(protected, google_code)
    translated = pm.restore(translated)

    dest_dir = TAB_GUIDE_DIR / target_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(translated)

    if not quiet:
        safe_print(f'  Saved: {dest_path}')
        safe_print(f'  Done!')

    return (filename, target_dir, True, str(dest_path))


def translate_all():
    print('\n' + '=' * 60)
    print('  TAB GUIDE HTML TRANSLATOR (PARALLEL)')
    print('  Translating HTML files to all supported languages')
    print('=' * 60)

    if not TAB_GUIDE_SRC.exists():
        print(f'\nError: Source directory not found at {TAB_GUIDE_SRC}')
        return False

    html_files = sorted([f.name for f in TAB_GUIDE_SRC.iterdir() if f.suffix == '.html'])
    if not html_files:
        print(f'\nError: No HTML files found in {TAB_GUIDE_SRC}')
        return False

    print(f'\n  Found {len(html_files)} HTML files:')
    for f in html_files:
        print(f'    - {f}')
    print(f'\n  Translating to {len(LANGUAGES)} languages...')
    for file_code, info in LANGUAGES.items():
        print(f"    - {info['name']} ({info['code']}) -> {info['dir']}/")
    print()

    start_time = time.time()

    tasks = []
    for fname in html_files:
        for file_code, info in LANGUAGES.items():
            tasks.append((fname, info['dir'], info['code'], info['name']))

    results = []
    with ThreadPoolExecutor(max_workers=min(len(tasks), 10)) as executor:
        future_to_task = {
            executor.submit(translate_html_file, fname, tdir, gcode, lname, quiet=True):
            (fname, tdir, lname)
            for fname, tdir, gcode, lname in tasks
        }
        for future in as_completed(future_to_task):
            fname, tdir, lname = future_to_task[future]
            try:
                result = future.result()
                results.append(result)
                safe_print(f'  \u2713 {fname} -> {tdir}/ ({lname})')
            except Exception as e:
                safe_print(f'  \u2717 {fname} -> {tdir}/ ({lname}) failed: {e}')
                results.append((fname, tdir, False, str(e)))

    elapsed_time = time.time() - start_time
    print('\n' + '=' * 60)
    print('  TRANSLATION SUMMARY')
    print('=' * 60)
    success_count = sum(1 for _, _, s, _ in results if s)
    print(f'  Total: {success_count}/{len(results)} successful')
    print(f'  Time: {elapsed_time:.1f} seconds')
    return success_count == len(results)


def translate_language(file_code: str):
    if file_code not in LANGUAGES:
        print(f"Error: Unknown language code '{file_code}'")
        print(f"Available: {', '.join(LANGUAGES.keys())}")
        return False

    info = LANGUAGES[file_code]
    if not TAB_GUIDE_SRC.exists():
        print(f'Error: Source directory not found at {TAB_GUIDE_SRC}')
        return False

    html_files = sorted([f.name for f in TAB_GUIDE_SRC.iterdir() if f.suffix == '.html'])
    print(f'\nTranslating {len(html_files)} files to {info["name"]} ({info["code"]})...')

    all_ok = True
    for fname in html_files:
        result = translate_html_file(fname, info['dir'], info['code'], info['name'])
        if not result[2]:
            all_ok = False

    return all_ok


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Translate tab guide HTML files to supported languages')
    parser.add_argument('language', nargs='?', default='all',
                        help="Language code (e.g., zh_CN, de_DE). Use 'all' for all.")
    parser.add_argument('--list', '-l', action='store_true', help='List available languages')
    args = parser.parse_args()

    if args.list:
        print('\nAvailable languages:')
        for code, info in LANGUAGES.items():
            print(f'  {code}: {info["name"]} (dir: {info["dir"]}/, google: {info["code"]})')
        exit(0)

    if args.language == 'all':
        success = translate_all()
    else:
        success = translate_language(args.language)

    exit(0 if success else 1)
