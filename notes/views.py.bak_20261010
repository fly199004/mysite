"""notes 视图：知识库首页 / 领域 / 书架 / 书籍页 / 单篇 / 在线编辑 / 附件 / 旧URL 301。

浏览按可见性放行；编辑与保存仅 staff。
"""
import datetime
import mimetypes
import os

from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404, HttpResponseNotAllowed
from django.shortcuts import redirect, render

from . import services
from .section_meta import SECTIONS


# ---------------- 栏目页（三大板块） ----------------

def section_xuan(request):
    man = services.load_manifest()
    reading = services.visible_notes(
        [n for n in services.domain_notes('reading') if not n.get('book')], request.user)
    book_cards = []
    visible = services.visible_notes(man.get('notes', []), request.user)
    for b in man.get('books', []):
        count = sum(1 for n in visible if n.get('book') == b['id'])
        if count:
            book_cards.append({'book': b, 'count': count})
    return render(request, 'notes/section.html', {
        'section': SECTIONS['xuan'],
        'reading': reading,
        'book_cards': book_cards,
    })


def section_it(request):
    tech = services.visible_notes(
        [n for n in services.domain_notes('tech') if not n.get('book')], request.user)
    return render(request, 'notes/section.html', {
        'section': SECTIONS['it'],
        'tech': tech,
    })


def section_teach(request):
    notes = services.visible_notes(services.domain_notes('teach'), request.user)
    return render(request, 'notes/section.html', {
        'section': SECTIONS['teach'],
        'teach': notes,
    })


# ---------------- 知识库首页 ----------------

def index(request):
    man = services.load_manifest()
    visible = services.visible_notes(man.get('notes', []), request.user)

    def _ind_count(domain_id):
        return sum(1 for n in visible if n.get('domain') == domain_id and not n.get('book'))

    def _latest_date(domain_id):
        ns = [n for n in visible if n.get('domain') == domain_id and not n.get('book')]
        return ns[0].get('date', '') if ns else ''

    book_total = sum(1 for n in visible if n.get('book'))

    def _card(meta, count, latest, url):
        return {'title': meta['title'], 'title_en': meta.get('title_en', ''),
                'icon': meta.get('icon', ''), 'subtitle': meta.get('subtitle', ''),
                'intro': meta.get('intro', ''), 'count': count,
                'latest': latest, 'url': url}

    ai_meta = {'title': 'AI资讯', 'title_en': 'AI Daily News', 'icon': 'robot',
               'subtitle': '每日 AI 动态',
               'intro': '每日 AI 最新新闻与行业动态速递：大模型发布、行业大事件、新产品与实用工具。'}
    cards = [
        _card(SECTIONS['xuan'], _ind_count('reading') + book_total,
              _latest_date('reading'), '/notes/xuan/'),
        _card(ai_meta, _ind_count('ai-news'),
              _latest_date('ai-news'), '/notes/ai-news/'),
        _card(SECTIONS['it'], _ind_count('tech'),
              _latest_date('tech'), '/notes/it/'),
        _card(SECTIONS['teach'], _ind_count('teach'),
              _latest_date('teach'), '/notes/teach/'),
    ]
    return render(request, 'notes/index.html', {
        'cards': cards,
        'total': len(visible),
    })


# ---------------- 领域页 ----------------

def domain_detail(request, domain_id):
    d = services.get_domain(domain_id)
    if not d:
        raise Http404
    notes = [n for n in services.domain_notes(domain_id) if not n.get('book')]
    notes = services.visible_notes(notes, request.user)
    books = []
    for b in services.load_manifest().get('books', []):
        if any(n.get('book') == b['id'] and n.get('domain') == domain_id
               for n in services.book_notes(b['id'])):
            books.append(b)
    return render(request, 'notes/domain.html',
                  {'domain': d, 'notes': notes, 'books': books})


# ---------------- 旧 URL 301 ----------------

def legacy_redirect(request, domain_id, legacy_id):
    n = services.get_note_by_legacy(domain_id, legacy_id)
    if not n or not services.can_view(n, request.user):
        raise Http404
    return redirect('notes:detail', slug=n['slug'], permanent=True)


# ---------------- 书架 ----------------

def books(request):
    man = services.load_manifest()
    visible = services.visible_notes(man.get('notes', []), request.user)
    cards = []
    for b in man.get('books', []):
        count = sum(1 for n in visible if n.get('book') == b['id'])
        if count:
            cards.append({'book': b, 'count': count})
    return render(request, 'notes/books.html', {'cards': cards})


# ---------------- 书籍页 ----------------

def book_detail(request, book_id):
    b = services.get_book(book_id)
    if not b:
        raise Http404
    chapters = services.visible_notes(services.book_notes(b['id']), request.user)
    return render(request, 'notes/book_detail.html',
                  {'book': b, 'chapters': chapters})


# ---------------- 单篇 ----------------

def note_detail(request, slug):
    note = services.get_note(slug)
    if not note or not services.can_view(note, request.user):
        raise Http404
    text = services.strip_frontmatter(services.read_note_text(note))
    text = services.strip_leading_h1(text)
    text = services.strip_title_h1(text, note.get('title', ''))
    html, toc = services.render_markdown(text)
    prev_n, next_n = services.siblings(slug)
    if prev_n and not services.can_view(prev_n, request.user):
        prev_n = None
    if next_n and not services.can_view(next_n, request.user):
        next_n = None
    b = services.get_book(note.get('book'))
    domain = services.get_domain(note.get('domain')) if not b else None
    return render(request, 'notes/detail.html', {
        'note': note, 'html': html, 'toc': toc,
        'prev_n': prev_n, 'next_n': next_n, 'book': b, 'domain': domain,
    })


# ---------------- 在线编辑（仅 staff） ----------------

@staff_member_required
def note_edit(request, slug):
    note = services.get_note(slug)
    if not note:
        raise Http404
    raw = services.read_note_text(note)
    return render(request, 'notes/edit.html', {'note': note, 'raw': raw})


@staff_member_required
def note_save(request, slug):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    note = services.get_note(slug)
    if not note:
        raise Http404
    content = request.POST.get('content', '')
    path = services.safe_resolve(note['file'])

    if os.path.isfile(path):
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        bak = path + '.bak_' + stamp
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())

    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp, path)

    services.load_manifest(force=True)
    return redirect('notes:detail', slug=slug)


# ---------------- 附件服务 ----------------

SAFE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.pdf'}


def asset(request, path):
    full = services.safe_resolve(os.path.join('assets', path))
    if not os.path.isfile(full):
        raise Http404
    if os.path.splitext(full)[1].lower() not in SAFE_EXTS:
        raise Http404
    ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
    if os.path.splitext(full)[1].lower() == '.webp':
        ctype = 'image/webp'
    return FileResponse(open(full, 'rb'), content_type=ctype)
