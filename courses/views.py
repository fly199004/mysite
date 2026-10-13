from urllib.parse import urlencode

from django.shortcuts import redirect, render

from . import services

UTM = {"utm_source": "liufeisheng", "utm_medium": "courses", "utm_campaign": "feiyun"}


def _with_utm(url):
    if not url:
        return url
    sep = "&" if "?" in url else "?"
    return url + sep + urlencode(UTM)


def _track_name(tid):
    for t in services.tracks():
        if t["id"] == tid:
            return t["name"]
    return ""


def course_list(request):
    groups = services.grouped_for_list()
    shorts = [c for c in services.visible_courses() if c.get("kind") == "short"]
    shorts.sort(key=lambda x: x.get("order", 0), reverse=True)
    featured = [c for c in services.visible_courses()
                if c.get("featured") and c.get("kind") != "short"]
    featured.sort(key=lambda x: x.get("order", 0), reverse=True)
    ctx = {
        "groups": groups,
        "shorts": shorts,
        "featured": featured,
        "tracks": services.tracks(),
        "stats": services.stats(),
    }
    return render(request, "courses/course_list.html", ctx)


def course_detail(request, course_id):
    course = services.get_course(course_id)
    if course is None or not course.get("show", True):
        from django.http import Http404
        raise Http404("课程不存在或未发布")

    links = []
    for l in (course.get("links") or []):
        item = dict(l)
        item["utm_url"] = _with_utm(l.get("url", ""))
        links.append(item)

    # 右栏：同分类（track）其他在架课程，最多 6 门
    related = [c for c in services.visible_courses()
               if c.get("track") == course.get("track")
               and c.get("id") != course_id]
    related.sort(key=lambda x: x.get("order", 0), reverse=True)
    related = related[:6]

    ctx = {
        "course": course,
        "links": links,
        "has_link": any(l.get("url") for l in links),
        "embed_url": services.embed_url(course) if services.has_embed(course) else "",
        "track_name": _track_name(course.get("track")),
        "related": related,
    }
    return render(request, "courses/course_detail.html", ctx)


def course_go(request, course_id):
    """外链中转：/courses/go/<id>/?to=B站 → 302 到真实平台地址。"""
    course = services.get_course(course_id)
    if course is None or not course.get("show", True):
        from django.http import Http404
        raise Http404("课程不存在或未发布")

    want = request.GET.get("to", "").strip()
    chosen = None
    for l in (course.get("links") or []):
        if l.get("url") and (not want or l.get("platform") == want):
            chosen = l
            break
    if not chosen:
        return redirect("courses:course_detail", course_id=course_id)
    return redirect(_with_utm(chosen["url"]))
