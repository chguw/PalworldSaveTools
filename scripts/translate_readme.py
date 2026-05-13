import re
import os
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
try:
    from deep_translator import GoogleTranslator
except ImportError:
    print('Installing deep-translator...')
    import subprocess
    subprocess.check_call(['pip', 'install', 'deep-translator'])
    from deep_translator import GoogleTranslator
PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_SOURCE = PROJECT_ROOT / 'README.md'
README_DIR = PROJECT_ROOT / 'resources' / 'readme'
LANGUAGES = {'zh_CN': {'name': 'Simplified Chinese', 'code': 'zh-CN'}, 'de_DE': {'name': 'German', 'code': 'de'}, 'es_ES': {'name': 'Spanish', 'code': 'es'}, 'fr_FR': {'name': 'French', 'code': 'fr'}, 'ru_RU': {'name': 'Russian', 'code': 'ru'}, 'ja_JP': {'name': 'Japanese', 'code': 'ja'}, 'ko_KR': {'name': 'Korean', 'code': 'ko'}}
TRANSLATIONS = {'zh_CN': {'title': 'Palworld 的综合保存文件编辑工具包', 'download_text': '从', 'download_link': '下载独立版本', 'toc': '目录', 'features': '特点', 'installation': '安装', 'quick_start': '快速入门', 'tools_overview': '工具概述', 'guides': '指南', 'troubleshooting': '故障排除', 'building': '构建独立可执行文件', 'contributing': '贡献', 'license': '许可证', 'back_to_top': '返回顶部', 'made_with_love': '用 ❤️ 为 Palworld 社区制作'}, 'de_DE': {'title': 'Ein umfassendes Toolkit zur Bearbeitung gespeicherter Dateien für Palworld', 'download_text': 'Laden Sie die Standalone-Version von', 'download_link': 'herunter', 'toc': 'Inhaltsverzeichnis', 'features': 'Funktionen', 'installation': 'Installation', 'quick_start': 'Schnellstart', 'tools_overview': 'Tools-Übersicht', 'guides': 'Anleitungen', 'troubleshooting': 'Fehlerbehebung', 'building': 'Erstellen einer eigenständigen ausführbaren Datei', 'contributing': 'Mitwirken', 'license': 'Lizenz', 'back_to_top': 'Nach oben', 'made_with_love': 'Hergestellt mit ❤️ für die Palworld-Community'}, 'es_ES': {'title': 'Un kit de herramientas completo para editar archivos de guardado de Palworld', 'download_text': 'Descarga la versión independiente de', 'download_link': '', 'toc': 'Índice', 'features': 'Características', 'installation': 'Instalación', 'quick_start': 'Inicio rápido', 'tools_overview': 'Descripción de herramientas', 'guides': 'Guías', 'troubleshooting': 'Solución de problemas', 'building': 'Compilar ejecutable independiente', 'contributing': 'Contribuir', 'license': 'Licencia', 'back_to_top': 'Volver arriba', 'made_with_love': 'Hecho con ❤️ para la comunidad de Palworld'}, 'fr_FR': {'title': "Une boîte à outils complète pour l'édition de fichiers de sauvegarde Palworld", 'download_text': 'Téléchargez la version autonome depuis', 'download_link': '', 'toc': 'Table des matières', 'features': 'Fonctionnalités', 'installation': 'Installation', 'quick_start': 'Démarrage rapide', 'tools_overview': 'Aperçu des outils', 'guides': 'Guides', 'troubleshooting': 'Dépannage', 'building': "Compiler l'exécutable autonome", 'contributing': 'Contribuer', 'license': 'Licence', 'back_to_top': 'Retour en haut', 'made_with_love': 'Fait avec ❤️ pour la communauté Palworld'}, 'ru_RU': {'title': 'Комплексный набор инструментов для редактирования файлов сохранений Palworld', 'download_text': 'Скачайте автономную версию с', 'download_link': '', 'toc': 'Содержание', 'features': 'Возможности', 'installation': 'Установка', 'quick_start': 'Быстрый старт', 'tools_overview': 'Обзор инструментов', 'guides': 'Руководства', 'troubleshooting': 'Устранение неполадок', 'building': 'Сборка автономного исполняемого файла', 'contributing': 'Участие', 'license': 'Лицензия', 'back_to_top': 'Наверх', 'made_with_love': 'Создано с ❤️ для сообщества Palworld'}, 'ja_JP': {'title': 'Palworld 用の包括的なセーブファイル編集ツールキット', 'download_text': 'スタンドアロン バージョンを', 'download_link': 'からダウンロードします', 'toc': '目次', 'features': '特徴', 'installation': 'インストール', 'quick_start': 'クイックスタート', 'tools_overview': 'ツールの概要', 'guides': 'ガイド', 'troubleshooting': 'トラブルシューティング', 'building': 'スタンドアロン実行可能ファイルのビルド', 'contributing': '貢献する', 'license': 'ライセンス', 'back_to_top': 'トップに戻る', 'made_with_love': 'Palworld コミュニティのために ❤️ で作成されました'}, 'ko_KR': {'title': 'Palworld를 위한 포괄적인 저장 파일 편집 툴킷', 'download_text': '', 'download_link': '에서 독립형 버전을 다운로드하세요', 'toc': '목차', 'features': '기능', 'installation': '설치', 'quick_start': '빠른 시작', 'tools_overview': '도구 개요', 'guides': '가이드', 'troubleshooting': '문제 해결', 'building': '독립형 실행 파일 빌드', 'contributing': '기여', 'license': '라이센스', 'back_to_top': '맨 위로', 'made_with_love': 'Palworld 커뮤니티를 위해 ❤️으로 제작'}}
HEADER_SECTION = '<div align="center">\n\n![PalworldSaveTools Logo](../PalworldSaveTools_Blue.png)\n\n# PalworldSaveTools\n\n**{title}**\n\n[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)\n[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)\n[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)\n[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)\n\n[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)\n\n---\n\n### **{download_text} [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** {download_link}\n\n---\n\n</div>\n'
SECTION_HEADERS = ['Features', 'Installation', 'Quick Start', 'Tools Overview', 'Guides', 'Troubleshooting', 'Building Standalone Executable', 'Contributing', 'License']
CODE_BLOCK_PATTERN = re.compile('```[\\s\\S]*?```', re.MULTILINE)
INLINE_CODE_PATTERN = re.compile('`[^`]+`')
URL_PATTERN = re.compile('https?://[^\\s\\)\\]>"]+')
ANCHOR_LINK_PATTERN = re.compile('\\[([^\\]]+)\\]\\(#[^\\)]+\\)')
MD_LINK_PATTERN = re.compile('\\[([^\\]]+)\\]\\([^\\)]+\\)')
IMAGE_PATTERN = re.compile('!\\[([^\\]]*)\\]\\([^\\)]+\\)')
HTML_TAG_PATTERN = re.compile('<(?:details|summary|div|align|br|hr|table|tr|td|th|thead|tbody|ul|ol|li|p|a|img|strong|b|em|i|code|pre|span|sub|sup|h[1-6])[^>]*>', re.IGNORECASE)
HTML_CLOSING_TAG_PATTERN = re.compile('</(?:details|summary|div|table|tr|td|th|thead|tbody|ul|ol|li|p|a|strong|b|em|i|code|pre|span|sub|sup|h[1-6])>', re.IGNORECASE)
class PlaceholderManager:
    def __init__(self):
        self.placeholders: Dict[str, str] = {}
        self.counter = 0
    def add(self, text: str, prefix: str='P') -> str:
        key = f'__{prefix}{self.counter}__'
        self.placeholders[key] = text
        self.counter += 1
        return key
    def restore(self, text: str) -> str:
        def get_counter(item):
            key = item[0]
            match = re.search('(\\d+)', key)
            return int(match.group(1)) if match else 0
        for key, value in sorted(self.placeholders.items(), key=lambda x: -get_counter(x)):
            text = text.replace(key, value)
        return text
    def clear(self):
        self.placeholders = {}
        self.counter = 0
def protect_code_blocks(text: str, pm: PlaceholderManager) -> str:
    def replace_code(match):
        return pm.add(match.group(0), 'C')
    return CODE_BLOCK_PATTERN.sub(replace_code, text)
def protect_inline_code(text: str, pm: PlaceholderManager) -> str:
    def replace_inline(match):
        return pm.add(match.group(0), 'I')
    return INLINE_CODE_PATTERN.sub(replace_inline, text)
def protect_urls(text: str, pm: PlaceholderManager) -> str:
    def replace_url(match):
        return pm.add(match.group(0), 'U')
    return URL_PATTERN.sub(replace_url, text)
def protect_images(text: str, pm: PlaceholderManager) -> str:
    def replace_img(match):
        return pm.add(match.group(0), 'M')
    return IMAGE_PATTERN.sub(replace_img, text)
def protect_markdown_links(text: str, pm: PlaceholderManager) -> str:
    def replace_link(match):
        full = match.group(0)
        if '](' in full and '(#' in full:
            return full
        return pm.add(full, 'L')
    return MD_LINK_PATTERN.sub(replace_link, text)
def protect_anchor_links(text: str, pm: PlaceholderManager) -> str:
    toc_start = text.find('## Table of Contents')
    if toc_start == -1:
        toc_start = text.find('## 目次')
    if toc_start != -1:
        toc_end_pattern = re.compile('\\n## ', re.MULTILINE)
        toc_end_match = toc_end_pattern.search(text, toc_start + 10)
        if toc_end_match:
            before_toc = text[:toc_start]
            toc_section = text[toc_start:toc_end_match.start()]
            after_toc = text[toc_end_match.start():]
            def replace_anchor(match):
                return pm.add(match.group(0), 'A')
            before_toc = ANCHOR_LINK_PATTERN.sub(replace_anchor, before_toc)
            after_toc = ANCHOR_LINK_PATTERN.sub(replace_anchor, after_toc)
            return before_toc + toc_section + after_toc
    def replace_anchor(match):
        return pm.add(match.group(0), 'A')
    return ANCHOR_LINK_PATTERN.sub(replace_anchor, text)
def protect_html_tags(text: str, pm: PlaceholderManager) -> str:
    def replace_tag(match):
        return pm.add(match.group(0), 'H')
    result = HTML_TAG_PATTERN.sub(replace_tag, text)
    result = HTML_CLOSING_TAG_PATTERN.sub(replace_tag, result)
    return result
def protect_platform_terms(text: str, pm: PlaceholderManager) -> str:
    platform_terms = ['Discord', 'GitHub', 'Steam', 'GamePass', 'NexusMods', 'Wiki', 'uv']
    protected_text = text
    for term in platform_terms:
        pattern = re.compile(re.escape(term))
        def replace_platform(match):
            return pm.add(match.group(0), 'P')
        protected_text = pattern.sub(replace_platform, protected_text)
    return protected_text
def protect_game_terms(text: str, pm: PlaceholderManager) -> str:
    game_terms = ['Pal Editor', '\\bpals?\\b', '\\bPal\\b', '\\bIVs\\b', '\\bIV\\b', 'passives', 'private chests', 'PalworldSaveTools']
    for term in sorted(game_terms, key=len, reverse=True):
        pattern = re.compile(term, re.IGNORECASE)
        def replace_game(match):
            return pm.add(match.group(0), 'G')
        text = pattern.sub(replace_game, text)
    return text
def protect_common_terms(text: str, pm: PlaceholderManager) -> str:
    common_terms = [('private', '\\bprivate\\b')]
    for term, pattern_str in common_terms:
        pattern = re.compile(pattern_str)
        def replace_common(match):
            return pm.add(match.group(0), 'C')
        text = pattern.sub(replace_common, text)
    return text
def generate_anchor_id(text: str) -> str:
    anchor = text.lower().strip()
    anchor = re.sub('[^\\w\\s-]', '', anchor, flags=re.UNICODE)
    anchor = re.sub('\\s+', '-', anchor)
    anchor = re.sub('-+', '-', anchor)
    return anchor
def extract_toc_section(content: str) -> Tuple[str, str]:
    toc_pattern = re.compile('(## Table of Contents\\s*\\n(?:-+\\s*\\n)?)(.*?)(?=\\n---\\s*\\n## )', re.DOTALL)
    match = toc_pattern.search(content)
    if match:
        toc_header = match.group(1)
        toc_body = match.group(2)
        remaining = content[:match.start()] + content[match.end():]
        return (toc_header, toc_body, remaining)
    return ('', '', content)
def build_toc_from_content(content: str, lang_code: str) -> str:
    translations = TRANSLATIONS.get(lang_code, {})
    heading_pattern = re.compile('^## ([^\\n]+)', re.MULTILINE)
    headings = heading_pattern.findall(content)
    toc_lines = [f"## {translations.get('toc', 'Table of Contents')}", '']
    for heading in headings:
        if heading.lower() in ['table of contents', translations.get('toc', '').lower()]:
            continue
        anchor = generate_anchor_id(heading)
        toc_lines.append(f'- [{heading}](#{anchor})')
    return '\n'.join(toc_lines)
def split_text_for_translation(text: str, max_length: int=4500) -> List[str]:
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
def translate_text(text: str, target_lang: str, source_lang: str='en') -> str:
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
def extract_content_after_header(content: str) -> str:
    header_end_pattern = re.compile('</div>\\s*\\n', re.MULTILINE)
    match = header_end_pattern.search(content)
    if match:
        return content[match.end():]
    return content
def fix_section_anchors(content: str) -> str:
    def fix_heading(match):
        level = match.group(1)
        text = match.group(2).strip()
        return f'{level} {text}'
    return re.sub('^(#{2,3})\\s+(.+)$', fix_heading, content, flags=re.MULTILINE)
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
def translate_readme(target_lang_code: str, target_file_code: str, lang_name: str, quiet: bool=False):
    if not quiet:
        safe_print(f"\n{'=' * 50}")
        safe_print(f'Translating to {lang_name} ({target_lang_code})...')
        safe_print(f"{'=' * 50}")
    with open(README_SOURCE, 'r', encoding='utf-8') as f:
        content = f.read()
    translations = TRANSLATIONS.get(target_file_code, {})
    header = HEADER_SECTION.format(title=translations.get('title', 'A comprehensive save file editing toolkit for Palworld'), download_text=translations.get('download_text', 'Download the standalone version from'), download_link=translations.get('download_link', ''))
    body_content = extract_content_after_header(content)
    pm = PlaceholderManager()
    protected = protect_code_blocks(body_content, pm)
    protected = protect_inline_code(protected, pm)
    protected = protect_images(protected, pm)
    protected = protect_urls(protected, pm)
    protected = protect_markdown_links(protected, pm)
    protected = protect_anchor_links(protected, pm)
    protected = protect_html_tags(protected, pm)
    protected = protect_platform_terms(protected, pm)
    protected = protect_game_terms(protected, pm)
    if not quiet:
        safe_print(f'  Protected {len(pm.placeholders)} elements')
        safe_print(f'  Translating body content...')
    translated = translate_text(protected, target_lang_code)
    translated = pm.restore(translated)
    translated = re.sub('\\!\\[([^\\]]*)\\]\\(resources/', '![\\1](../', translated)
    translated = re.sub('^(#{2,4})[ \\u00a0\\t]?', '\\1 ', translated, flags=re.MULTILINE)
    translated = re.sub('^(#{2,4})([^\\s#])', '\\1 \\2', translated, flags=re.MULTILINE)
    toc_header = translations.get('toc', 'Table of Contents')
    heading_pattern = re.compile('^## ([^\\n]+)', re.MULTILINE)
    headings = heading_pattern.findall(translated)
    new_toc_items = []
    toc_variants = ['table of contents', 'contents', '目录', 'inhaltsverzeichnis', 'índice', 'indice', 'table des matières', 'содержание', '目次', '목차', 'tabla de contenidos']
    excluded_sections = ['disclaimer', '免責事項', '免责声明', '면책조항', 'haftungsausschluss', 'descargo de responsabilidad', 'exonération de responsabilité', 'avertissement', 'отказ от ответственности', 'support', 'サポート', '지원', '支持', 'unterstützung', 'soporte', 'soutien', 'assistance', 'поддержка', 'acknowledgments', '謝辞', '致谢', 'danksagungen', 'agradecimientos', 'remerciements', 'благодарности', '감사의 말씀']
    for heading in headings:
        heading_lower = heading.lower().strip()
        if heading_lower in [v.lower() for v in toc_variants]:
            continue
        if any((excl in heading_lower for excl in excluded_sections)):
            continue
        anchor = generate_anchor_id(heading)
        new_toc_items.append(f'- [{heading}](#{anchor})')
    new_toc_text = '\n'.join(new_toc_items)
    toc_pattern = re.compile('^## [^\\n]+\\n+(?:-+\\n+)?(?:- \\[[^\\]]+\\]\\([^)]+\\)\\n)+', re.MULTILINE)
    new_toc_section = f'\n## {toc_header}\n\n{new_toc_text}\n'
    translated = toc_pattern.sub(new_toc_section, translated, count=1)
    final_content = header + translated
    output_path = README_DIR / f'README.{target_file_code}.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    if not quiet:
        safe_print(f'  Saved to: {output_path}')
        safe_print(f'  Done!')
    return (target_file_code, True, str(output_path))
def translate_all():
    print('\n' + '=' * 60)
    print('  README AUTO-TRANSLATOR (PARALLEL)')
    print('  Translating README.md to all supported languages')
    print('=' * 60)
    if not README_SOURCE.exists():
        print(f'\nError: Source README not found at {README_SOURCE}')
        return False
    README_DIR.mkdir(parents=True, exist_ok=True)
    print(f'\n  Translating {len(LANGUAGES)} languages in parallel...')
    for lang_code, lang_info in LANGUAGES.items():
        print(f"    - {lang_info['name']} ({lang_info['code']})")
    print()
    start_time = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=len(LANGUAGES)) as executor:
        future_to_lang = {executor.submit(translate_readme, lang_info['code'], lang_code, lang_info['name'], quiet=True): (lang_code, lang_info['name']) for lang_code, lang_info in LANGUAGES.items()}
        for future in as_completed(future_to_lang):
            lang_code, lang_name = future_to_lang[future]
            try:
                result = future.result()
                results.append(result)
                safe_print(f'  ✓ {lang_name} ({lang_code}) completed')
            except Exception as e:
                safe_print(f'  ✗ {lang_name} ({lang_code}) failed: {e}')
                results.append((lang_code, False, str(e)))
    elapsed_time = time.time() - start_time
    print('\n' + '=' * 60)
    print('  TRANSLATION SUMMARY')
    print('=' * 60)
    results.sort(key=lambda x: list(LANGUAGES.keys()).index(x[0]) if x[0] in LANGUAGES else 999)
    for lang_code, success, info in results:
        status = 'SUCCESS' if success else 'FAILED'
        print(f'  {lang_code}: {status}')
    success_count = sum((1 for _, s, _ in results if s))
    print(f'\n  Total: {success_count}/{len(results)} successful')
    print(f'  Time: {elapsed_time:.1f} seconds')
    return all((s for _, s, _ in results))
def translate_single(lang_code: str):
    if lang_code not in LANGUAGES:
        print(f"Error: Unknown language code '{lang_code}'")
        print(f"Available: {', '.join(LANGUAGES.keys())}")
        return False
    lang_info = LANGUAGES[lang_code]
    return translate_readme(lang_info['code'], lang_code, lang_info['name'])
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Translate README.md to supported languages')
    parser.add_argument('language', nargs='?', default='all', help="Language code to translate (e.g., zh_CN, de_DE). Use 'all' for all languages.")
    parser.add_argument('--list', '-l', action='store_true', help='List available languages')
    args = parser.parse_args()
    if args.list:
        print('\nAvailable languages:')
        for code, info in LANGUAGES.items():
            print(f"  {code}: {info['name']}")
        exit(0)
    if args.language == 'all':
        success = translate_all()
    else:
        success = translate_single(args.language)
    exit(0 if success else 1)