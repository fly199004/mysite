"""课堂点名积分：页面 + JSON 接口。
查询（GET）免登录；所有写操作必须登录（accounts 中间件兜底 + login_required）。"""
import json
import secrets
import time

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

from .models import Classroom, Current


def _get_current_id():
    cur = Current.objects.using("classroom").first()
    return cur.class_id if cur else ""


def _set_current_id(class_id):
    cur = Current.objects.using("classroom").first()
    if cur:
        cur.class_id = class_id
        cur.save(using="classroom")
    else:
        Current.objects.using("classroom").create(class_id=class_id)


def _room_payload(room):
    try:
        state = json.loads(room.state or "{}")
    except Exception:
        state = {}
    return {"id": room.class_id, "name": room.name, "state": state}


def _all_payload():
    rooms = list(Classroom.objects.using("classroom").all())
    return {
        "currentClassId": _get_current_id(),
        "classes": [_room_payload(r) for r in rooms],
    }


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


def index(request):
    """课堂点名页面。"""
    return render(request, "classroom/index.html", {})


@require_http_methods(["GET"])
def list_classes(request):
    return JsonResponse(_all_payload())


@login_required(login_url="/accounts/login/")
@require_http_methods(["POST"])
def create_class(request):
    data = _json_body(request)
    name = str(data.get("name", "")).strip()
    if not name:
        return JsonResponse({"detail": "班级名称不能为空"}, status=400)
    cid = "c" + format(time.time_ns(), "x") + secrets.token_hex(2)
    state = data.get("state", {})
    room = Classroom.objects.using("classroom").create(
        class_id=cid, name=name, state=json.dumps(state, ensure_ascii=False))
    _set_current_id(cid)
    return JsonResponse(_room_payload(room))


@login_required(login_url="/accounts/login/")
@require_http_methods(["PUT"])
def rename_class(request, class_id):
    data = _json_body(request)
    try:
        room = Classroom.objects.using("classroom").get(class_id=class_id)
    except Classroom.DoesNotExist:
        return JsonResponse({"detail": "班级不存在"}, status=404)
    name = str(data.get("name", "")).strip()
    if not name:
        return JsonResponse({"detail": "班级名称不能为空"}, status=400)
    if Classroom.objects.using("classroom").filter(name=name).exclude(
            class_id=class_id).exists():
        return JsonResponse({"detail": "已存在同名班级"}, status=409)
    room.name = name
    room.save(using="classroom", update_fields=["name", "updated_at"])
    return JsonResponse({"ok": True})


@login_required(login_url="/accounts/login/")
@require_http_methods(["PUT"])
def state_class(request, class_id):
    data = _json_body(request)
    try:
        room = Classroom.objects.using("classroom").get(class_id=class_id)
    except Classroom.DoesNotExist:
        return JsonResponse({"detail": "班级不存在"}, status=404)
    state = data.get("state", {})
    room.state = json.dumps(state, ensure_ascii=False)
    room.save(using="classroom", update_fields=["state", "updated_at"])
    return JsonResponse({"ok": True})


@login_required(login_url="/accounts/login/")
@require_http_methods(["DELETE"])
def delete_class(request, class_id):
    deleted, _ = Classroom.objects.using("classroom").filter(class_id=class_id).delete()
    if not deleted:
        return JsonResponse({"detail": "班级不存在"}, status=404)
    if _get_current_id() == class_id:
        first = Classroom.objects.using("classroom").first()
        _set_current_id(first.class_id if first else "")
    return JsonResponse({"ok": True})


@login_required(login_url="/accounts/login/")
@require_http_methods(["PUT"])
def current(request):
    data = _json_body(request)
    cid = str(data.get("currentClassId", "")).strip()
    if cid and not Classroom.objects.using("classroom").filter(class_id=cid).exists():
        return JsonResponse({"detail": "班级不存在"}, status=404)
    _set_current_id(cid)
    return JsonResponse({"ok": True})


@login_required(login_url="/accounts/login/")
@require_http_methods(["POST"])
def replace_all(request):
    data = _json_body(request)
    classes = data.get("classes")
    if not isinstance(classes, list):
        return JsonResponse({"detail": "classes 必须是数组"}, status=400)

    Classroom.objects.using("classroom").all().delete()
    Current.objects.using("classroom").all().delete()

    count = 0
    for item in classes:
        cid = str(item.get("id", "")).strip()
        name = str(item.get("name", "")).strip()
        if not cid or not name:
            continue
        state = item.get("state", {})
        Classroom.objects.using("classroom").create(
            class_id=cid, name=name, state=json.dumps(state, ensure_ascii=False))
        count += 1

    cid = str(data.get("currentClassId", "")).strip()
    if cid and Classroom.objects.using("classroom").filter(class_id=cid).exists():
        _set_current_id(cid)
    else:
        first = Classroom.objects.using("classroom").first()
        _set_current_id(first.class_id if first else "")

    return JsonResponse({"ok": True, "count": count})


def health(request):
    return JsonResponse({"ok": True})
