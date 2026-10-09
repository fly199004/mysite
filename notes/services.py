"""notes 服务层：发布区读写、路径安全、Markdown 渲染。

发布区根目录由 settings.NOTES_ROOT 指定，仅文件系统操作，不建数据库。
所有文件读取都必须经 safe_resolve()，杜绝路径穿越。
"""
import os
import re
import json
import threading

import markdown
from django.conf import settings
from django.http import Http404

_md_lock = threading.Lock()
_manifest_cache = {'mtime': None, 'data': None}


# ---------------- manifest ----------------

def _manifest_path():
    return os.path.join(str(settings.NOTES_ROOT), 'manifest.json')


def load_manifest(force=False):
    """读取并缓存 manifest.json（按文件 mtime 失效）。"""
    path = _manifest_path()
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        raise Http404('manifest.json 不存在')
    if not force and _manifest_cache['data'] is not None and _manifest_cache['mtime'] == mtime:
        return _manifest_cache['data']
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    _manifest_cache['mtime'] = mtime
    _manifest_cache['data'] = data
    return data


def get_book(book_id):
    for b in load_manifest().get('books', []):
        if b.get('id') == book_id:
            return b
    return None


def get_domain(domain_id):
    for d in load_manifest().get('domains', []):
        if d.get('id') == domain_id:
            return d
    return None


def all_notes():
    return load_manifest().get('notes', [])


def latest_independent_notes(domain_id=None, limit=8):
    """最新独立文章（日期倒序）。domain_id 给定时只取该领域。"""
    notes = [n for n in all_notes() if not n.get('book')
             and (domain_id is None or n.get('domain') == domain_id)]
    notes.sort(key=lambda n: (n.get('date') or '', n.get('order', 0)), reverse=True)
    return notes[:limit]


def domain_notes(domain_id):
    """某领域下全部笔记（未过滤可见性）。

    书型章节排在前（保持书籍自身 order）；
    独立文章按日期倒序（最新在前），无日期者靠后。
    """
    out = [n for n in all_notes() if n.get('domain') == domain_id]
    books_ = [n for n in out if n.get('book')]
    indep = [n for n in out if not n.get('book')]
    books_.sort(key=lambda n: n.get('order', 0))
    indep.sort(key=lambda n: (n.get('date') or '', n.get('order', 0)), reverse=True)
    return books_ + indep


def book_notes(book_id):
    out = [n for n in all_notes() if n.get('book') == book_id]
    out.sort(key=lambda n: n.get('order', 0))
    return out


def get_note_by_legacy(domain_id, legacy_id):
    """按旧数字 id 定位笔记（用于旧 URL 301）。"""
    try:
        lid = int(legacy_id)
    except (TypeError, ValueError):
        return None
    for n in all_notes():
        if n.get('domain') == domain_id and n.get('legacy_id') == lid:
            return n
    return None


def get_note(slug):
    for n in load_manifest().get('notes', []):
        if n.get('slug') == slug:
            return n
    return None


def visible_notes(notes, user):
    """按可见性与登录态过滤。

    public : 任何人
    login  : 仅登录用户
    private: 仅 staff
    """
    out = []
    for n in notes:
        v = n.get('visibility', 'public')
        if v == 'public':
            out.append(n)
        elif v == 'login' and getattr(user, 'is_authenticated', False):
            out.append(n)
        elif v == 'private' and getattr(user, 'is_staff', False):
            out.append(n)
    return out


def can_view(note, user):
    v = note.get('visibility', 'public')
    if v == 'public':
        return True
    if v == 'login':
        return getattr(user, 'is_authenticated', False)
    if v == 'private':
        return getattr(user, 'is_staff', False)
    return False


# ---------------- 文件与路径 ----------------

def safe_resolve(rel_path):
    """把发布区内的相对路径解析为绝对路径，并校验仍在发布区内。"""
    root = os.path.realpath(str(settings.NOTES_ROOT))
    target = os.path.realpath(os.path.join(root, rel_path))
    if target != root and not target.startswith(root + os.sep):
        raise Http404('非法路径')
    return target


def read_note_text(note):
    path = safe_resolve(note['file'])
    if not os.path.isfile(path):
        raise Http404('正文文件不存在')
    with open(path, encoding='utf-8', errors='ignore') as f:
        return f.read()


# 去掉正文开头的 frontmatter（导出型 md 含 YAML 头）
_FRONMATTER = re.compile(r'^\s*---\r?\n.*?\r?\n---\r?\n+', re.S)

# 去掉正文开头的首个 H1（页面已单独用主题标题渲染，避免重复）
_LEADING_H1 = re.compile(r'^\s*#\s+.+?\s*(?:\r?\n)+', re.S)


def strip_frontmatter(text):
    return _FRONMATTER.sub('', text, count=1)


def strip_leading_h1(text):
    return _LEADING_H1.sub('', text, count=1)


def strip_title_h1(text, title):
    """移除正文中所有与页面标题相同的 H1（迁移文内可能重复出现）。"""
    if not title:
        return text
    pat = re.compile(r'^[ \t]*#\s*' + re.escape(title.strip()) + r'\s*(?:\r?\n)+',
                     re.M)
    return pat.sub('', text)


# ---------------- Markdown 渲染 ----------------

def render_markdown(text):
    with _md_lock:
        md = markdown.Markdown(
            extensions=['extra', 'toc', 'sane_lists'],
            extension_configs={'toc': {'title': None}},
        )
        html = md.convert(text)
        toc = md.toc
    return html, toc


# ---------------- 章节导航 ----------------

def siblings(slug):
    """返回 (上一篇, 下一篇)。

    书型笔记：按 book.note_order；
    领域型笔记：按同领域 order(legacy_id)。
    """
    cur = get_note(slug)
    if not cur:
        return None, None
    by_slug = {n['slug']: n for n in all_notes()}

    if cur.get('book'):
        book = get_book(cur['book'])
        order = [s for s in book.get('note_order', []) if s in by_slug] if book else []
    else:
        seq = domain_notes(cur.get('domain'))
        order = [n['slug'] for n in seq if not n.get('book')]

    if slug not in order:
        return None, None
    i = order.index(slug)
    prev_n = by_slug[order[i - 1]] if i > 0 else None
    next_n = by_slug[order[i + 1]] if i < len(order) - 1 else None
    return prev_n, next_n
