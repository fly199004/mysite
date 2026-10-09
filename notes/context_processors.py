"""全局上下文：为左侧栏提供「分栏目」导航。

三个栏目：
  xuan   飞云轩 Reading   —— 阅读记录 + 书架
  it     IT技术 Technology —— AI资讯 + IT记录
  teach  IT教学 Teaching  —— 教学笔记

根据当前请求所在路径 / 文章所属领域推断栏目，只显示该栏目相关分组。
只读取发布区 manifest，不触发数据库；异常时静默降级。
"""
from . import services

# 路径前缀 -> 栏目
_PATH_MAP = {
    '/notes/xuan': 'xuan',
    '/notes/it': 'it',
    '/notes/teach': 'teach',
    '/notes/reading': 'xuan',
    '/notes/ai-news': 'it',
    '/notes/tech': 'it',
    '/notes/books': 'xuan',
}

# 领域 -> 栏目
_DOMAIN_MAP = {
    'reading': 'xuan',
    'ai-news': 'it',
    'tech': 'it',
    'teach': 'teach',
}


def _resolve_section(path):
    for prefix, sec in _PATH_MAP.items():
        if path.startswith(prefix):
            return sec
    return None


def _latest(domain_id, limit):
    return services.visible_notes(
        services.latest_independent_notes(domain_id, limit), None)


def _build_groups(section):
    groups = []
    if section == 'xuan':
        groups.append({
            'kind': 'list', 'id': 'reading', 'title': '阅读记录',
            'icon': 'fa-book', 'all_url': '/notes/reading/',
            'notes': _latest('reading', 10),
        })
        groups.append({
            'kind': 'books', 'id': 'books', 'title': '书架专题',
            'icon': 'fa-th-large', 'all_url': '/notes/books/',
            'books': services.load_manifest().get('books', []),
        })
    elif section == 'it':
        groups.append({
            'kind': 'list', 'id': 'tech', 'title': 'IT记录',
            'icon': 'fa-code', 'all_url': '/notes/tech/',
            'notes': _latest('tech', 10),
        })
    elif section == 'teach':
        notes = services.visible_notes(services.domain_notes('teach'), None)
        groups.append({
            'kind': 'list', 'id': 'teach', 'title': '教学笔记',
            'icon': 'fa-chalkboard-teacher', 'all_url': '/notes/teach/',
            'notes': notes[:12],
        })
    return groups


def knowledge_sidebar(request):
    section = _resolve_section(request.path)

    # 单篇文章页：路径是 /notes/<slug>/，需按文章领域推断栏目
    note = None
    if section is None and request.path.startswith('/notes/'):
        slug = request.path.strip('/').split('/')
        if len(slug) >= 2 and slug[1] not in ('', 'asset', 'legacy'):
            note = services.get_note(slug[1])
            if note:
                section = _DOMAIN_MAP.get(note.get('domain'))

    if not section:
        return {}

    try:
        groups = _build_groups(section)
    except Exception:
        groups = []

    return {'kb_sidebar': groups, 'kb_section': section}


def home_sidebar(request):
    """站点首页（/ 或 /index/）左侧栏：AI资讯、IT技术、飞云阅读 各前3篇。"""
    if request.path not in ('/', '/index/'):
        return {}
    try:
        groups = [
            {'kind': 'list', 'title': 'AI资讯', 'icon': 'fa-robot',
             'all_url': '/notes/ai-news/', 'notes': _latest('ai-news', 3)},
            {'kind': 'list', 'title': 'IT技术', 'icon': 'fa-laptop-code',
             'all_url': '/notes/it/', 'notes': _latest('tech', 3)},
            {'kind': 'list', 'title': '飞云阅读', 'icon': 'fa-feather-alt',
             'all_url': '/notes/xuan/', 'notes': _latest('reading', 3)},
        ]
    except Exception:
        groups = []
    return {'home_sidebar': groups}
