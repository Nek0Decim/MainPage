#!/usr/bin/env python3
"""Lokalny panel redakcyjny dla statycznej strony RPG. Tylko standardowa biblioteka Python 3.10+."""
from __future__ import annotations

import base64
import datetime as dt
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
import sys
import threading
import unicodedata
from urllib.parse import parse_qs, quote, unquote, urlparse
import webbrowser

ROOT = Path(__file__).resolve().parent
EDITOR = ROOT / 'editor'
SOURCES = ROOT / 'content' / 'articles'
DRAFTS = ROOT / '.szkice-lokalne'
PAGES = ROOT / 'wpisy'
COVERS = ROOT / 'images' / 'blog'
PUB_FILE = ROOT / 'content' / 'publications.json'
LEGACY_FILE = ROOT / 'content' / 'legacy-articles.json'
SITE_DATA = ROOT / 'tworczosc-data.js'
TOKEN = secrets.token_urlsafe(24)
CATEGORIES = ('Warsztat MG', 'Projektowanie narracji', 'Kulisy twórczości')

for directory in (SOURCES, DRAFTS, PAGES, COVERS):
    directory.mkdir(parents=True, exist_ok=True)


def jload(path, fallback):
    try:
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else fallback
    except (ValueError, OSError):
        return fallback


def write_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(content, encoding='utf-8')
    os.replace(temp, path)


def save_json(path, obj):
    write_atomic(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def slugify(text):
    text = unicodedata.normalize('NFKD', text.replace('ł', 'l').replace('Ł', 'L'))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()
    return text[:75]


def safe_slug(value):
    return bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value or '')) and len(value) <= 80


def js_object_import():
    """Import known previous edition content without third-party JS parsers.

    Existing publication information is preserved even when user already edited the JS.
    Handles serializable object literals (quoted strings, bare identifier keys, comments).
    """
    if not SITE_DATA.exists():
        return {'publications': [], 'articles': []}
    s = SITE_DATA.read_text(encoding='utf-8')
    m = re.search(r'window\.TWORCZOSC_CONTENT\s*=\s*\{', s)
    if not m:
        return {'publications': [], 'articles': []}
    start = s.index('{', m.start())
    # Strip JS // comments, preserving escaped strings and URLs.
    cleaned = []
    in_string = None
    escaped = False
    i = start
    depth = 0
    while i < len(s):
        c = s[i]
        if in_string:
            cleaned.append(c)
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == in_string:
                in_string = None
            i += 1
            continue
        if c in ('"', "'"):
            in_string = c
            cleaned.append(c)
            i += 1
            continue
        if s[i:i+2] == '//':
            i = s.find('\n', i)
            if i == -1:
                break
            cleaned.append('\n')
            i += 1
            continue
        if s[i:i+2] == '/*':
            i = s.find('*/', i+2)
            if i == -1:
                break
            i += 2
            continue
        if c == '{':
            depth += 1
        if c == '}':
            depth -= 1
        cleaned.append(c)
        i += 1
        if depth == 0:
            break
    s = ''.join(cleaned)
    s = re.sub(r'([\{,]\s*)([a-zA-Z_$][\w$]*)\s*:', r'\1"\2":', s)
    s = re.sub(r',\s*([}\]])', r'\1', s)
    try:
        result = json.loads(s)
        return result if isinstance(result, dict) else {'publications': [], 'articles': []}
    except ValueError:
        raise ValueError('Nie udało się odczytać istniejącego tworczosc-data.js. Zachowano go bez zmian; sprawdź składnię.')


def initial_content():
    # One-time safe import of previous website data; do not overwrite data already configured.
    current = js_object_import()
    if not PUB_FILE.exists():
        pubs = current.get('publications') or []
        save_json(PUB_FILE, [{**p, 'id': str(p.get('id') or secrets.token_hex(8))} for p in pubs if isinstance(p, dict) and str(p.get('title', '')).strip()])
    if not LEGACY_FILE.exists():
        legacy = current.get('articles') or []
        existing_links = {f'wpisy/{p.stem}.html' for p in SOURCES.glob('*.json')}
        save_json(LEGACY_FILE, [a for a in legacy if isinstance(a, dict) and a.get('url') not in existing_links])


IMPORT_ERROR = ''
try:
    initial_content()
except ValueError as err:
    IMPORT_ERROR = str(err)


def markdown_inline(src):
    # Render a deliberately restricted Markdown subset. Raw HTML is escaped.
    # Links only accept http(s), mailto, hash and safe relative pages.
    code_chunks = []
    def code_placeholder(match):
        code_chunks.append('<code>' + html.escape(match.group(1)) + '</code>')
        return f'ZCODEPLACEHOLDER{len(code_chunks)-1}Z'
    src = re.sub(r'`([^`\n]+)`', code_placeholder, src)
    src = html.escape(src, quote=True)
    def replace_link(match):
        name, url = match.group(1), html.unescape(match.group(2).strip())
        if not (url.startswith(('https://','http://','mailto:','#')) or re.fullmatch(r'[\w./#%-]+', url)):
            return name
        return f'<a href="{html.escape(url, quote=True)}" rel="noopener noreferrer">{name}</a>'
    src = re.sub(r'\[([^\[\]\n]{1,160})\]\(([^()\n]{1,350})\)', replace_link, src)
    src = re.sub(r'\*\*([^*\n]+)\*\*', r'<strong>\1</strong>', src)
    src = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', src)
    for i, tag in enumerate(code_chunks):
        src = src.replace(f'ZCODEPLACEHOLDER{i}Z', tag)
    return src


def markdown_to_html(body):
    """Tiny dependency-free renderer for headings, lists, quotes, code, paragraphs."""
    lines = body.replace('\r\n','\n').replace('\r','\n').split('\n')
    out = []
    paragraph = []
    current_list = None
    in_code = False
    code_lines = []
    def finish_paragraph():
        if paragraph:
            out.append('<p>' + '<br>'.join(markdown_inline(p) for p in paragraph) + '</p>')
            paragraph.clear()
    def finish_list():
        nonlocal current_list
        if current_list:
            out.append(f'</{current_list}>')
            current_list = None
    for line in lines:
        trim = line.strip()
        if trim.startswith('```'):
            finish_paragraph(); finish_list()
            if in_code:
                out.append('<pre><code>' + html.escape('\n'.join(code_lines)) + '</code></pre>')
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line); continue
        if not trim:
            finish_paragraph(); finish_list(); continue
        if trim == '---':
            finish_paragraph(); finish_list(); out.append('<hr>'); continue
        mh = re.match(r'^(#{1,3})\s+(.+)', trim)
        if mh:
            finish_paragraph(); finish_list()
            level = max(2, len(mh.group(1)))
            out.append(f'<h{level}>{markdown_inline(mh.group(2))}</h{level}>'); continue
        mq = re.match(r'^>\s?(.*)', trim)
        if mq:
            finish_paragraph(); finish_list()
            out.append('<blockquote><p>'+markdown_inline(mq.group(1))+'</p></blockquote>'); continue
        ml = re.match(r'^(?:[-*+]\s+|([0-9]+)\.\s+)(.+)', trim)
        if ml:
            finish_paragraph()
            list_type = 'ol' if ml.group(1) is not None else 'ul'
            if current_list != list_type:
                finish_list(); out.append(f'<{list_type}>'); current_list = list_type
            out.append('<li>'+markdown_inline(ml.group(2))+'</li>'); continue
        finish_list()
        paragraph.append(trim)
    finish_paragraph(); finish_list()
    if in_code:
        out.append('<pre><code>' + html.escape('\n'.join(code_lines)) + '</code></pre>')
    return '\n'.join(out)


def fmt_date(date):
    try:
        day = dt.date.fromisoformat(date)
        months = ['', 'stycznia','lutego','marca','kwietnia','maja','czerwca','lipca','sierpnia','września','października','listopada','grudnia']
        return f'{day.day} {months[day.month]} {day.year}'
    except ValueError:
        return date


def safe_cover(value):
    return value if isinstance(value, str) and re.fullmatch(r'images/blog/[a-zA-Z0-9_.-]+\.(?:png|jpe?g|webp)', value) else ''


def article_html(post):
    title = html.escape(post['title'])
    lead = html.escape(post['lead'])
    cat = html.escape(post['category'])
    date = html.escape(post['publishedAt'])
    date_nice = html.escape(fmt_date(post['publishedAt']))
    cover = safe_cover(post.get('cover', ''))
    image = f'<figure class="article-cover"><img src="../{html.escape(cover, quote=True)}" alt="Ilustracja do artykułu: {title}"></figure>' if cover else ''
    content = markdown_to_html(post['body'])
    meta_img = f'<meta property="og:image" content="../{html.escape(cover, quote=True)}">' if cover else '<meta property="og:image" content="../logo-red.png">'
    return f'''<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#63191d">
  <meta name="description" content="{html.escape(post['lead'], quote=True)}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{html.escape(post['title'], quote=True)}">
  <meta property="og:description" content="{html.escape(post['lead'], quote=True)}">
  {meta_img}
  <title>{title} | Zapiski Mistrza Gry</title>
  <link rel="icon" href="../logo-red.png" type="image/png">
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Crimson+Text:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../style.css">
  <link rel="stylesheet" href="../home.css">
  <link rel="stylesheet" href="../artykul.css">
</head>
<body class="home-page single-article-page">
  <a class="skip-link" href="#tresc">Przejdź do treści</a>
  <header class="site-header"><div class="site-header__inner">
    <a href="../index.html" class="site-brand"><img src="../logo-red.png" width="74" height="74" alt=""><span class="site-brand__text"><span class="site-brand__name">Jakub Kamiński</span><span class="site-brand__subtitle">Mistrz Gry · Narracja · Wrocław</span></span></a>
    <a class="header-contact" href="../tworczosc.html#zapiski">Wszystkie artykuły ↗</a>
  </div></header>
  <nav class="site-nav" aria-label="Nawigacja główna"><div class="site-nav__desktop">
    <a href="../index.html">Start</a><a href="../sesje-prywatne.html">Sesje prywatne</a><a href="../repertuar.html">Repertuar</a><a href="../pracownia-narracji.html">Pracownia Narracji</a><a href="../tworczosc.html" class="is-current">Twórczość</a><a href="../o-mnie.html">O mnie</a><a href="../faq.html">FAQ</a>
  </div><details class="site-nav__mobile"><summary>Menu <span aria-hidden="true">☰</span></summary><div class="site-nav__mobile-links">
    <a href="../index.html">Start</a><a href="../sesje-prywatne.html">Sesje prywatne</a><a href="../repertuar.html">Repertuar</a><a href="../pracownia-narracji.html">Pracownia Narracji</a><a href="../tworczosc.html">Twórczość</a><a href="../o-mnie.html">O mnie</a><a href="../faq.html">FAQ</a>
  </div></details></nav>
  <main id="tresc"><div class="article-band"><div class="layout-wrap"><a href="../tworczosc.html#zapiski" class="article-back">← Wszystkie zapiski</a><p class="article-kicker">{cat} <span>✦</span> {date_nice}</p><h1>{title}</h1><p class="article-lead">{lead}</p></div></div>
  <div class="layout-wrap article-layout">{image}<article class="article-body">{content}</article><div class="article-bottom"><span>Jakub Kamiński · Zapiski Mistrza Gry</span><a href="../tworczosc.html#zapiski">Wróć do artykułów ↗</a></div></div>
  </main><footer class="site-footer"><div class="layout-wrap site-footer__inner"><div class="site-footer__brand"><img src="../logo-red.png" alt=""><div><strong>Jakub Kamiński</strong><span>Mistrz Gry · Narracja · Wrocław</span></div></div><div class="site-footer__links"><a href="../index.html">Start</a><a href="../tworczosc.html">Twórczość</a><a href="../faq.html">FAQ</a><a href="../zrodla-zdjec.html">Źródła</a></div><p class="site-footer__copyright">© 2026 Jakub Kamiński · Sesje RPG</p><p class="site-footer__attribution">Zdjęcia stockowe: <a href="https://www.magnific.com/" target="_blank" rel="noopener noreferrer">Designed by Magnific</a> · <a href="../zrodla-zdjec.html">pełna lista źródeł</a></p></div></footer>
</body>
</html>
'''


def list_posts():
    entries = []
    for directory, status in ((SOURCES, 'published'), (DRAFTS, 'draft')):
        for f in directory.glob('*.json'):
            value = jload(f, None)
            if isinstance(value, dict):
                entries.append({**value, 'status': status})
    return sorted(entries, key=lambda p: (p.get('updatedAt',''),p.get('publishedAt','')), reverse=True)


def article_meta(post):
    words = len(post['body'].split())
    return {'title': post['title'], 'category': post['category'],
            'publishedAt': post['publishedAt'], 'lead': post['lead'],
            'url': 'wpisy/'+post['slug']+'.html', 'readTime': f'{max(1, math.ceil(words/200))} min',
            'cover': post.get('cover','')}


def regenerate():
    if IMPORT_ERROR:
        raise ValueError(IMPORT_ERROR)
    pubs = jload(PUB_FILE, [])
    old = jload(LEGACY_FILE, [])
    generated = []
    for file in sorted(SOURCES.glob('*.json')):
        post = jload(file, None)
        if not isinstance(post, dict):
            continue
        write_atomic(PAGES / (post['slug']+'.html'), article_html(post))
        generated.append(article_meta(post))
    taken = {a['url'] for a in generated}
    articles = generated + [a for a in old if a.get('url') not in taken]
    articles.sort(key=lambda p: str(p.get('publishedAt','')), reverse=True)
    data = {'publications': pubs, 'articles': articles}
    write_atomic(SITE_DATA, '/* Dane zarządzane przez lokalny edytor; nie trzeba edytować ręcznie. */\nwindow.TWORCZOSC_CONTENT = '+json.dumps(data, ensure_ascii=False, indent=2)+';\n')
    return {'articles': len(articles), 'publications': len(pubs)}


def validate_article(data):
    title = str(data.get('title','')).strip()
    if not (3 <= len(title) <= 160):
        raise ValueError('Tytuł musi mieć od 3 do 160 znaków.')
    slug = str(data.get('slug') or slugify(title)).strip().lower()
    if not safe_slug(slug):
        raise ValueError('Adres wpisu może zawierać tylko małe litery a–z, cyfry i myślniki.')
    category = data.get('category','Warsztat MG')
    if category not in CATEGORIES:
        raise ValueError('Nieznana kategoria artykułu.')
    date = data.get('publishedAt') or dt.date.today().isoformat()
    try:
        dt.date.fromisoformat(date)
    except ValueError:
        raise ValueError('Podaj datę w formacie RRRR-MM-DD.')
    lead = str(data.get('lead','')).strip()
    body = str(data.get('body','')).strip()
    if len(lead) > 500 or len(body) > 250000:
        raise ValueError('Zbyt długa zajawka lub treść artykułu.')
    cover = safe_cover(data.get('cover',''))
    return {'id': str(data.get('id') or secrets.token_hex(8)), 'slug':slug, 'title':title,
            'category':category, 'publishedAt':date, 'lead':lead, 'body':body, 'cover':cover,
            'updatedAt':dt.datetime.now().isoformat(timespec='seconds')}


def save_post(data, publish):
    post = validate_article(data)
    identity = post['id']
    # Match by id: slug cannot silently change on published entries (avoid abandoned files).
    existing = next((p for p in list_posts() if p.get('id') == identity), None)
    if existing and existing['status']=='published' and existing['slug'] != post['slug']:
        raise ValueError('Adres już opublikowanego wpisu pozostaje stały. Zmień tytuł, nie adres.')
    if not existing and (SOURCES/(post['slug']+'.json')).exists():
        raise ValueError('Ten adres jest już zajęty przez inny wpis.')
    if any(p['slug']==post['slug'] and p.get('id')!=identity for p in list_posts()):
        raise ValueError('Istnieje już wpis o tym adresie.')
    if publish:
        if IMPORT_ERROR:
            raise ValueError(IMPORT_ERROR)
        if len(post['lead']) < 15 or len(post['body']) < 30:
            raise ValueError('Przed publikacją dodaj zajawkę (min. 15 znaków) i treść (min. 30 znaków).')
        save_json(SOURCES/(post['slug']+'.json'), post)
        (DRAFTS/(post['slug']+'.json')).unlink(missing_ok=True)
        if existing and existing['status']=='draft' and existing['slug']!=post['slug']:
            (DRAFTS/(existing['slug']+'.json')).unlink(missing_ok=True)
        regenerate()
    else:
        if existing and existing['status']=='published':
            # Explicit save for published post keeps it published and synchronizes html.
            if len(post['lead']) < 15 or len(post['body']) < 30:
                raise ValueError('Opublikowany wpis musi zawierać zajawkę i treść.')
            save_json(SOURCES/(post['slug']+'.json'), post)
            regenerate()
        else:
            save_json(DRAFTS/(post['slug']+'.json'), post)
            if existing and existing['slug']!=post['slug']:
                (DRAFTS/(existing['slug']+'.json')).unlink(missing_ok=True)
    return {**post, 'status': 'published' if publish or (existing and existing['status']=='published') else 'draft'}


def unpublish(data):
    identity = data.get('id','')
    existing = next((p for p in list_posts() if p.get('id') == identity and p['status']=='published'), None)
    if not existing:
        raise ValueError('Nie znaleziono opublikowanego artykułu.')
    slug = existing['slug']
    # Copies source to local drafts; removes public page and listing.
    save_json(DRAFTS/(slug+'.json'), {k:v for k,v in existing.items() if k!='status'})
    (SOURCES/(slug+'.json')).unlink(missing_ok=True)
    (PAGES/(slug+'.html')).unlink(missing_ok=True)
    regenerate()
    return {'ok':True}


def delete_draft(data):
    identity = data.get('id','')
    existing = next((p for p in list_posts() if p.get('id') == identity and p['status']=='draft'), None)
    if not existing:
        raise ValueError('Można usunąć tylko szkic.')
    (DRAFTS/(existing['slug']+'.json')).unlink(missing_ok=True)
    return {'ok':True}


def validate_publication(pub):
    title = str(pub.get('title','')).strip()
    if not 2 <= len(title) <= 160:
        raise ValueError('Podaj tytuł publikacji (2–160 znaków).')
    url = str(pub.get('url','')).strip()
    if url and not re.fullmatch(r'https://[^\s<>"\']+', url):
        raise ValueError('Link do publikacji musi zaczynać się od https://')
    return {'id': str(pub.get('id') or secrets.token_hex(8)), 'title':title,
            'system':str(pub.get('system','')).strip()[:100],
            'format':str(pub.get('format','')).strip()[:80],
            'description':str(pub.get('description','')).strip()[:1000],
            'cover':safe_cover(pub.get('cover','')), 'url':url}


def save_publication(data):
    if IMPORT_ERROR:
        raise ValueError(IMPORT_ERROR)
    pub = validate_publication(data)
    pubs = jload(PUB_FILE, [])
    match = next((i for i,p in enumerate(pubs) if p.get('id')==pub['id']), None)
    if match is None:
        pubs.append(pub)
    else:
        pubs[match] = pub
    save_json(PUB_FILE, pubs)
    regenerate()
    return pub


def delete_publication(data):
    pubs = jload(PUB_FILE, [])
    length = len(pubs)
    pubs = [p for p in pubs if p.get('id') != data.get('id')]
    if len(pubs) == length:
        raise ValueError('Nie znaleziono publikacji.')
    save_json(PUB_FILE, pubs)
    regenerate()
    return {'ok':True}


class Handler(BaseHTTPRequestHandler):
    server_version = 'RPGEditor/1.0'
    def log_message(self, format, *args):
        if '/api/' in self.path:
            return
        super().log_message(format, *args)

    def _headers(self, code=200, content_type='application/json; charset=utf-8', length=None):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; script-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'")
        if length is not None:
            self.send_header('Content-Length', str(length))
        self.end_headers()

    def _json(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self._headers(status, length=len(data))
        self.wfile.write(data)

    def authorized(self):
        parsed = urlparse(self.path)
        if self.headers.get('X-Editor-Key', '') != TOKEN:
            return False
        origin = self.headers.get('Origin')
        expected = f'http://127.0.0.1:{self.server.server_port}'
        return origin is None or origin == expected

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ('/', '/index.html'):
            name = 'index.html'
        elif parsed.path in ('/ui.css','/ui.js'):
            name = parsed.path.lstrip('/')
        elif parsed.path.startswith('/view/'):
            relative = parsed.path.removeprefix('/view/')
            if not re.fullmatch(r'[a-zA-Z0-9_./-]+', relative) or '..' in relative.split('/'):
                return self._json({'error':'Nieprawidłowa ścieżka.'}, 400)
            path = (ROOT / relative).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                return self._json({'error':'Nie znaleziono pliku.'}, 404)
            mime = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
            data = path.read_bytes()
            self._headers(200, mime, len(data))
            self.wfile.write(data)
            return
        elif parsed.path == '/api/data':
            return self._json({'key': TOKEN, 'articles': list_posts(),
                               'publications': jload(PUB_FILE, []), 'error': IMPORT_ERROR,
                               'categories': list(CATEGORIES)})
        else:
            return self._json({'error':'Nie znaleziono.'}, 404)
        path = EDITOR / name
        data = path.read_bytes()
        mime = mimetypes.guess_type(str(path))[0] or 'text/plain'
        self._headers(200, mime + '; charset=utf-8', len(data))
        self.wfile.write(data)

    def do_POST(self):
        if not self.authorized():
            return self._json({'error':'Brak uprawnień do zmiany danych.'}, 403)
        try:
            size = int(self.headers.get('Content-Length','0'))
        except ValueError:
            return self._json({'error':'Nieprawidłowy rozmiar.'}, 400)
        if size <= 0 or size > 3_000_000:
            return self._json({'error':'Dane są zbyt duże.'}, 413)
        parsed = urlparse(self.path)
        try:
            raw = self.rfile.read(size)
            if parsed.path == '/api/upload':
                file_name = unquote(parse_qs(parsed.query).get('name',[''])[0])
                ext = Path(file_name).suffix.lower()
                if ext not in ('.png','.jpg','.jpeg','.webp'):
                    raise ValueError('Dozwolone obrazy: PNG, JPG, WEBP (maks. 3 MB).')
                magic_ok = (ext == '.png' and raw.startswith(b'\x89PNG\r\n\x1a\n') or
                            ext in ('.jpg','.jpeg') and raw.startswith(b'\xff\xd8\xff') or
                            ext == '.webp' and raw.startswith(b'RIFF') and raw[8:12] == b'WEBP')
                if not magic_ok:
                    raise ValueError('Plik nie wygląda na poprawny obraz.')
                file_name = slugify(Path(file_name).stem) or 'obraz'
                result_name = f'{file_name}-{secrets.token_hex(4)}{ext}'
                (COVERS/result_name).write_bytes(raw)
                return self._json({'cover': 'images/blog/'+result_name})
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError('Nieprawidłowe dane.')
            handlers = {
                '/api/save-draft': lambda: save_post(data, False),
                '/api/publish': lambda: save_post(data, True),
                '/api/unpublish': lambda: unpublish(data),
                '/api/delete-draft': lambda: delete_draft(data),
                '/api/save-publication': lambda: save_publication(data),
                '/api/delete-publication': lambda: delete_publication(data),
                '/api/preview': lambda: {'html': markdown_to_html(str(data.get('body',''))[:250000])},
            }
            if parsed.path not in handlers:
                return self._json({'error':'Nieznana operacja.'}, 404)
            return self._json(handlers[parsed.path]())
        except (ValueError, KeyError, OSError) as exc:
            return self._json({'error':str(exc)}, 400)


def main():
    if '--check' in sys.argv:
        print('Edytor gotowy. Dostępne szkice:', len(list_posts()))
        return
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    addr = f'http://127.0.0.1:{server.server_port}/'
    print('EDYTOR RPG — działa tylko na Twoim komputerze')
    print('Otwórz:', addr)
    print('Aby zamknąć: Ctrl+C w terminalu.')
    threading.Timer(0.8, lambda: webbrowser.open(addr)).start()
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print('\nEdytor został zamknięty.')
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
