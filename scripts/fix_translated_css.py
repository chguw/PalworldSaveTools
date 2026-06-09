"""Fix translated HTML files: restore English CSS style blocks that
were mangled by translation, while keeping the translated body content."""
import os
import re

BASE = os.path.join(os.path.dirname(__file__), '..', 'resources', 'tab_guide')
EN_DIR = os.path.join(BASE, 'en')

STYLE_RE = re.compile(r'<style>.*?</style>', re.DOTALL)

def main():
    for lang in sorted(os.listdir(BASE)):
        lang_dir = os.path.join(BASE, lang)
        if not os.path.isdir(lang_dir) or lang in ('en', '__pycache__', '__init__.py'):
            continue
        for fname in sorted(os.listdir(lang_dir)):
            if not fname.endswith('.html'):
                continue
            en_path = os.path.join(EN_DIR, fname)
            lang_path = os.path.join(lang_dir, fname)
            if not os.path.exists(en_path):
                continue
            with open(en_path, 'r', encoding='utf-8') as f:
                en_html = f.read()
            with open(lang_path, 'r', encoding='utf-8') as f:
                lang_html = f.read()
            en_style = STYLE_RE.search(en_html)
            lang_style = STYLE_RE.search(lang_html)
            if en_style and lang_style:
                fixed = lang_html.replace(lang_style.group(0), en_style.group(0))
                if fixed != lang_html:
                    with open(lang_path, 'w', encoding='utf-8') as f:
                        f.write(fixed)
                    print(f'Fixed CSS: {lang}/{fname}')
                else:
                    print(f'No change: {lang}/{fname}')
            else:
                print(f'Skipped (no style): {lang}/{fname}')

if __name__ == '__main__':
    main()
