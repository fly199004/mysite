"""飞云课程：文件系统数据加载（courses_data.json），不建数据库、不 migrate。"""
import json
import functools
from pathlib import Path

from django.conf import settings

DATA_FILE = Path(getattr(settings, "BASE_DIR")) / "courses" / "courses_data.json"


@functools.lru_cache(maxsize=1)
def _load_raw():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def reload_data():
    """数据文件更新后清缓存（管理/排错用）。"""
    _load_raw.cache_clear()


def tracks():
    """返回导航用学科线（按 json 中顺序）。"""
    return _load_raw().get("tracks", [])


def all_courses():
    return _load_raw().get("courses", [])


def visible_courses():
    return [c for c in all_courses() if c.get("show", True)]


def get_course(course_id):
    for c in all_courses():
        if c.get("id") == course_id:
            return c
    return None


def _avail_links(course):
    return [l for l in (course.get("links") or []) if l.get("url")]


def primary_link(course):
    """课程的主跳转链接（第一条填了 url 的平台）。"""
    links = _avail_links(course)
    return links[0] if links else None


def has_embed(course):
    """是否可做 B 站站内嵌入（需要 bvid/aid）。"""
    b = course.get("bilibili") or {}
    return bool(b.get("bvid") or b.get("aid"))


def embed_url(course):
    """生成 B 站 iframe 地址。"""
    b = course.get("bilibili") or {}
    if b.get("bvid"):
        return "https://player.bilibili.com/player.html?bvid=%s&page=1&high_quality=1&danmaku=0" % b["bvid"]
    if b.get("aid"):
        return "https://player.bilibili.com/player.html?aid=%s&page=1&high_quality=1&danmaku=0" % b["aid"]
    return ""


def grouped_for_list():
    """按学科线分组（仅展示中），组内按 order 降序；返回 [(track, [courses])...]。"""
    courses = visible_courses()
    order_map = {t["id"]: i for i, t in enumerate(tracks())}

    groups = {}
    for c in courses:
        groups.setdefault(c.get("track", ""), []).append(c)

    result = []
    for t in tracks():
        items = groups.get(t["id"], [])
        if not items:
            continue
        items.sort(key=lambda x: x.get("order", 0), reverse=True)
        result.append((t, items))
    return result


def stats():
    courses = visible_courses()
    long_n = sum(1 for c in courses if c.get("kind") == "long")
    short_n = sum(1 for c in courses if c.get("kind") == "short")
    eps = sum(c.get("episodes") or 0 for c in courses if c.get("kind") == "long")
    return {"long": long_n, "short": short_n, "episodes": eps}


def platforms_present():
    """筛选用：出现过的平台（基于主平台字段，短视频单独归并）。"""
    seen = []
    for c in visible_courses():
        for l in (c.get("links") or []):
            p = l.get("platform")
            if p and p not in seen:
                seen.append(p)
    return seen
