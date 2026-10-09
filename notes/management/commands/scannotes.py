"""扫描发布区领域目录，自动生成 manifest.json。

约定（发布区 notes_content/）：
  <domain>/<slug>.md        独立文章（slug 取文件名，去掉 .md）
  articles/<slug>.md        书型章节（由 books 配置管理，不重复扫描为独立文）
  assets/                   附件（不索引）

文章 frontmatter（均可缺省，缺省则用文件名/扫描值推断）：
  ---
  title: 标题
  date: 2026-10-01
  domain: tech            # 缺省取所在目录名
  tags: [a, b]
  visibility: public      # public / login / private
  legacy_id: 12           # 旧数字 id（可选）
  ---

用法（容器内）：
  python manage.py scannotes            # 扫描并写入
  python manage.py scannotes --dry      # 仅预览不写
  python manage.py scannotes --check    # 校验 slug 唯一、文件存在
"""
import os
import re
import json
import datetime
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

# 领域元信息（目录名 -> 展示信息）
DOMAIN_META = {
    'reading': {'title': '阅读记录', 'title_en': 'Reading Notes', 'icon': 'book',
                'intro': '读书、观影后的感想与书摘。'},
    'tech': {'title': 'IT记录', 'title_en': 'Tech Notes', 'icon': 'code',
             'intro': '编程实践、新技术探索与日常技术问题解决记录（敏感信息已隐去）。'},
    'teach': {'title': 'IT教学', 'title_en': 'Teaching Notes', 'icon': 'chalkboard-teacher',
              'intro': '编程语言与项目实训的章节讲义、教学记录。'},
    'ai-news': {'title': 'AI资讯', 'title_en': 'AI Daily News', 'icon': 'robot',
                'intro': '每日 AI 最新新闻与行业动态速递。'},
}

# 不作为领域扫描的保留目录
RESERVED = {'assets', 'articles', 'books'}

FM_BLOCK=re.compile('^[ \\t]*---[ \\t]*\\r?\\n(.*?)\\r?\\n---[ \\t]*\\r?\\n?', re.S)
_DATE_RE = re.compile(r'^(\d{8})')


def parse_simple_yaml(block):
    """只解析我们需要的简单 key: value（支持单行列表 [a, b]），不引第三方 YAML。"""
    data = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or ':' not in line:
            continue
        key, _, val = line.partition(':')
        key = key.strip()
        val = val.strip()
        if val.startswith('[') and val.endswith(']'):
            items = [x.strip().strip('"\'') for x in val[1:-1].split(',') if x.strip()]
            data[key] = items
            continue
        if (val.startswith('"') and val.endswith('"')) or \
           (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        data[key] = val
    return data


def split_frontmatter(text):
    m = FM_BLOCK.match(text)
    if not m:
        return {}, text
    return parse_simple_yaml(m.group(1)), text[m.end():]


def infer_title_from_body(body, fallback):
    for line in body.splitlines():
        s = line.strip()
        if s.startswith('#'):
            return s.lstrip('#').strip()
    return fallback


class Command(BaseCommand):
    help = '扫描领域目录自动生成 manifest.json'

    def add_arguments(self, parser):
        parser.add_argument('--dry', action='store_true', help='只预览不写入')
        parser.add_argument('--check', action='store_true', help='只校验')

    def handle(self, *args, **opts):
        root = str(settings.NOTES_ROOT)
        if not os.path.isdir(root):
            self.stderr.write('NOTES_ROOT 不存在: %s' % root)
            return

        domains = []
        notes = []
        slug_seen = {}

        # 1) 扫描各领域目录
        for name in sorted(os.listdir(root)):
            dpath = os.path.join(root, name)
            if not os.path.isdir(dpath) or name in RESERVED or name.startswith('.'):
                continue
            meta = DOMAIN_META.get(name)
            if not meta:
                # 未登记目录：仍扫描但给默认名，提示补登记
                meta = {'title': name, 'title_en': name, 'icon': 'folder', 'intro': ''}
                self.stdout.write(self.style.WARNING('未登记领域目录(用默认元信息): %s' % name))
            domains.append(dict(id=name, **meta))

            for fn in sorted(os.listdir(dpath)):
                if not fn.lower().endswith('.md'):
                    continue
                slug = fn[:-3]
                fpath = os.path.join(dpath, fn)
                raw = open(fpath, encoding='utf-8', errors='ignore').read()
                fm, body = split_frontmatter(raw)

                if slug in slug_seen:
                    self.stderr.write('重复 slug: %s (%s, %s)' %
                                      (slug, slug_seen[slug], f'{name}/{fn}'))
                slug_seen[slug] = f'{name}/{fn}'

                title = fm.get('title') or infer_title_from_body(body, slug)
                date = fm.get('date', '')
                # 文件名以 8 位日期开头时补 date
                mdate = _DATE_RE.match(fn)
                if not date and mdate:
                    d = mdate.group(1)
                    date = f'{d[0:4]}-{d[4:6]}-{d[6:8]}'
                try:
                    order = int(fm.get('order', '') )
                except ValueError:
                    order = fm.get('legacy_id') and _safeint(fm['legacy_id']) or 0
                note = {
                    'slug': slug,
                    'file': f'{name}/{fn}',
                    'domain': fm.get('domain', name),
                    'title': title,
                    'date': str(date),
                    'tags': fm.get('tags', []) if isinstance(fm.get('tags', []), list) else [],
                    'book': None,
                    'order': order,
                    'visibility': fm.get('visibility', 'public'),
                }
                if 'legacy_id' in fm:
                    note['legacy_id'] = _safeint(fm['legacy_id'])
                notes.append(note)

        # 2) 书型结构：读取现有 books 配置并扫描 articles/
        manifest_path = os.path.join(root, 'manifest.json')
        old = {}
        if os.path.isfile(manifest_path):
            try:
                old = json.load(open(manifest_path, encoding='utf-8'))
            except Exception:
                old = {}
        books = old.get('books', [])
        # slug -> (book_id, order)：以各书 note_order 为权威
        slug_book = {}
        for b in books:
            for idx, sslug in enumerate(b.get('note_order', [])):
                slug_book[sslug] = (b.get('id'), idx + 1)
        art_dir = os.path.join(root, 'articles')
        book_notes = []
        if os.path.isdir(art_dir):
            for fn in sorted(os.listdir(art_dir)):
                if not fn.lower().endswith('.md'):
                    continue
                slug = fn[:-3]
                raw = open(os.path.join(art_dir, fn), encoding='utf-8', errors='ignore').read()
                fm, body = split_frontmatter(raw)
                mapped_bid, mapped_order = slug_book.get(slug, (None, 0))
                book_id = fm.get('book') or mapped_bid
                order = _safeint(fm.get('order', 0)) or mapped_order
                bn = {
                    'slug': slug, 'file': f'articles/{fn}',
                    'domain': fm.get('domain', 'reading'),
                    'book': book_id, 'order': order,
                    'title': fm.get('title') or infer_title_from_body(body, slug),
                    'date': str(fm.get('date', '')),
                    'tags': fm.get('tags', []) if isinstance(fm.get('tags', []), list) else [],
                    'visibility': fm.get('visibility', 'public'),
                }
                book_notes.append(bn)

        # 若旧 manifest 的 books 已定义 note_order，保持其顺序权威
        manifest = {
            'version': 2,
            'domains': domains,
            'books': books,
            'notes': book_notes + notes,
        }

        # 校验
        problems = []
        allslugs = [n['slug'] for n in manifest['notes']]
        if len(allslugs) != len(set(allslugs)):
            dup = {s for s in allslugs if allslugs.count(s) > 1}
            problems.append('重复 slug: %s' % dup)
        for n in manifest['notes']:
            if not os.path.isfile(os.path.join(root, n['file'])):
                problems.append('文件缺失: %s' % n['file'])

        self.stdout.write('domains=%d notes=%d (book %d + independent %d)' %
                          (len(domains), len(manifest['notes']),
                           len(book_notes), len(notes)))
        if problems:
            for p in problems:
                self.stdout.write(self.style.WARNING('CHECK: %s' % p))
        else:
            self.stdout.write(self.style.SUCCESS('check ok'))

        if opts['check']:
            return
        if opts['dry']:
            self.stdout.write(json.dumps(
                {'domains': [d['id'] for d in domains],
                 'counts': _counts(manifest)}, ensure_ascii=False, indent=1))
            return

        if os.path.isfile(manifest_path):
            bak = manifest_path + '.bak_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            shutil.copy(manifest_path, bak)
        json.dump(manifest, open(manifest_path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        self.stdout.write(self.style.SUCCESS('written manifest.json'))


def _safeint(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _counts(manifest):
    out = {}
    for n in manifest['notes']:
        key = n.get('domain') or '?'
        out[key] = out.get(key, 0) + 1
    return out
