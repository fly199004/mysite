"""课堂点名积分：页面 + JSON 接口。"""
import json
import secrets
import time

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

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


def _authorized(request):
    token = getattr(settings, "CLASSROOM_TOKEN", "")
    if not token:
        # 未配置口令时默认放行（不建议生产这样）
        return True
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        supplied = auth[7:].strip()
    else:
        supplied = request.headers.get("X-Admin-Token", "").strip()
    return secrets.compare_digest(supplied, str(token))


def _unauthorized():
    return JsonResponse({"detail": "口令不正确或缺失"}, status=401)


def index(request):
    """课堂点名页面。"""
    return render(request, "classroom/index.html", {})


def list_classes(request):
    if request.method != "GET":
        return JsonResponse({"detail": "方法不允许"}, status=405)
    return JsonResponse(_all_payload())


@csrf_exempt
def create_class(request):
    if request.method != "POST":
        return JsonResponse({"detail": "方法不允许"}, status=405)
    if not _authorized(request):
        return _unauthorized()
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


@csrf_exempt
def rename_class(request, class_id):
    if request.method != "PUT":
        return JsonResponse({"detail": "方法不允许"}, status=405)
    if not _authorized(request):
        return _unauthorized()
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


@csrf_exempt
def state_class(request, class_id):
    if request.method != "PUT":
        return JsonResponse({"detail": "方法不允许"}, status=405)
    if not _authorized(request):
        return _unauthorized()
    data = _json_body(request)
    try:
        room = Classroom.objects.using("classroom").get(class_id=class_id)
    except Classroom.DoesNotExist:
        return JsonResponse({"detail": "班级不存在"}, status=404)
    state = data.get("state", {})
    room.state = json.dumps(state, ensure_ascii=False)
    room.save(using="classroom", update_fields=["state", "updated_at"])
    return JsonResponse({"ok": True})


@csrf_exempt
def delete_class(request, class_id):
    if request.method != "DELETE":
        return JsonResponse({"detail": "方法不允许"}, status=405)
    if not _authorized(request):
        return _unauthorized()
    deleted, _ = Classroom.objects.using("classroom").filter(class_id=class_id).delete()
    if not deleted:
        return JsonResponse({"detail": "班级不存在"}, status=404)
    if _get_current_id() == class_id:
        first = Classroom.objects.using("classroom").first()
        _set_current_id(first.class_id if first else "")
    return JsonResponse({"ok": True})


@csrf_exempt
def current(request):
    if request.method != "PUT":
        return JsonResponse({"detail": "方法不允许"}, status=405)
    if not _authorized(request):
        return _unauthorized()
    data = _json_body(request)
    cid = str(data.get("currentClassId", "")).strip()
    if cid and not Classroom.objects.using("classroom").filter(class_id=cid).exists():
        return JsonResponse({"detail": "班级不存在"}, status=404)
    _set_current_id(cid)
    return JsonResponse({"ok": True})


@csrf_exempt
def replace_all(request):
    if request.method != "POST":
        return JsonResponse({"detail": "方法不允许"}, status=405)
    if not _authorized(request):
        return _unauthorized()
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
