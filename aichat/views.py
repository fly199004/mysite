"""AI 对话子页（/ai/）：Django 侧做登录校验 + 文件管理 + 流式转发到 Hermes / OpenCode。

设计说明（重要，改动前先读）：
- Hermes API Server 的 `model` 参数是**被忽略的**（实测传 totally-fake-model 照样 200），
  且 capabilities.admin_config_rw=false，所以无法按请求切换 Hermes 的底层模型。
- 因此本页提供两个后端：
  A) hermes：带完整工具（可读写上传的文件），模型由容器配置决定（= auto/auto-cn 那套）
  B) direct：直连 OpenCode Go 的 OpenAI 兼容端点，model 参数真实生效，可切 30+ 模型（无工具）
- 文件：上传到 /app/aichat_uploads/u<uid>/（宿主 /volume2/docker/mysite/aichat_uploads），
  同时 bind mount 到 hermes 容器的 /mnt/uploads，agent 用文件工具直接读。
- 密钥只从 /app/aichat_config.json 读取，不写在代码里。
"""
import json
import os
import re
import time

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import (FileResponse, Http404, HttpResponse, JsonResponse,
                         StreamingHttpResponse)
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

CONFIG_PATH = getattr(settings, "AICHAT_CONFIG_PATH", "/app/aichat_config.json")
UPLOAD_ROOT = getattr(settings, "AICHAT_UPLOAD_ROOT", "/app/aichat_uploads")
# agent 看到的上传目录（hermes 容器内的挂载点）
AGENT_UPLOAD_ROOT = "/mnt/uploads"

MAX_UPLOAD_BYTES = 50 * 1024 * 1024          # 单文件 50MB
SAFE_NAME_RE = re.compile(r"^[\w\u4e00-\u9fa5.\-()\[\] ]{1,120}$")

# 明确不可用的模型（实测：地区封锁 / 端点无此模型），不给前端选
BLOCKED_MODELS = {
    "beam-free",                # 403 RegionError: not available in your country
    "cat-jam-free",             # 403 RegionError
    "step-5-preview-free",      # 400 Model is unavailable
    "test",                     # 占位脏数据
}


def _cfg():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _user_dir(user):
    d = os.path.join(UPLOAD_ROOT, "u%d" % user.id)
    os.makedirs(d, exist_ok=True)
    return d


def _safe_name(raw):
    name = os.path.basename((raw or "").replace("\\", "/")).strip()
    if not name or not SAFE_NAME_RE.match(name):
        raise ValueError("文件名含不支持字符（仅允许中英文、数字、空格、. - _ ( ) [ ]，最多 120 字）")
    return name


# ─────────────────────────── 页面 ───────────────────────────
@login_required
def index(request):
    return render(request, "aichat/index.html", {
        "user_dir": "u%d" % request.user.id,
        "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
    })


# ─────────────────────────── 模型清单 ───────────────────────────
_model_cache = {"ts": 0, "direct": []}


def _direct_models():
    """从 OpenCode Go 拉真实模型清单，10 分钟缓存。失败则回退到内置常用清单。"""
    now = time.time()
    if _model_cache["direct"] and now - _model_cache["ts"] < 600:
        return _model_cache["direct"]
    fallback = ["deepseek-v4.1-flash", "deepseek-v4-pro", "glm-5.3", "glm-5.3-flash",
                "kimi-k3", "qwen3.8-max", "qwen3.8-flash", "minimax-m3",
                "grok-4.7", "gpt-6-luna", "claude-haiku-5-5"]
    try:
        cfg = _cfg()
        r = requests.get(cfg["opencode_url"] + "/models",
                         headers={"User-Agent": "hermes-aichat/1.0"}, timeout=15)
        r.raise_for_status()
        ids = [m.get("id") for m in r.json().get("data", []) if m.get("id")]
        ids = [i for i in ids if i not in BLOCKED_MODELS]
        if ids:
            _model_cache["direct"] = ids
            _model_cache["ts"] = now
            return ids
    except Exception:
        pass
    return fallback


@login_required
@require_GET
def api_models(request):
    direct = _direct_models()
    preferred = ["deepseek-v4.1-flash", "deepseek-v4-pro", "glm-5.3", "kimi-k3",
                 "qwen3.8-max", "grok-4.7", "minimax-m3"]
    ordered = [m for m in preferred if m in direct] + [m for m in direct if m not in preferred]
    return JsonResponse({
        "backends": [
            {"id": "hermes", "label": "Hermes Agent · 可读写文件/用工具",
             "note": "由 NAS 上 Hermes 容器作答，模型固定（当前 deepseek-v4.1-flash / opencode-go）"},
            {"id": "direct", "label": "直连模型 · 纯对话（可切模型）",
             "note": "直接调用 OpenCode Go，响应更快但没有工具能力"},
        ],
        "agent_model": "hermes-agent",
        "direct_models": ordered,
    })


# ─────────────────────────── 对话（SSE 透传） ───────────────────────────
@login_required
@require_POST
def api_chat(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"error": "请求体不是合法 JSON"}, status=400)

    mode = payload.get("mode") or "hermes"
    messages = payload.get("messages") or []
    attachments = payload.get("attachments") or []
    model = payload.get("model") or "deepseek-v4.1-flash"
    if not messages or not isinstance(messages, list):
        return JsonResponse({"error": "messages 不能为空"}, status=400)

    cfg = _cfg()

    if mode == "hermes":
        # 附件：把 agent 容器内可见路径告诉它
        if attachments:
            listing = "\n".join("- " + a for a in attachments)
            messages = [dict(m) for m in messages]
            messages[-1]["content"] = (
                (messages[-1].get("content") or "")
                + "\n\n[用户上传的附件已在 NAS 上，可直接用文件工具读取：]\n" + listing
                + "\n若要把生成的文件交给用户下载，请写入同一目录 %s/u%d/ 下，并告知文件名。"
                  % (AGENT_UPLOAD_ROOT, request.user.id)
            )
        url = cfg["hermes_url"].rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": "Bearer " + cfg["hermes_key"],
            "Content-Type": "application/json",
            "X-Hermes-Session-Key": "aichat:user:%d" % request.user.id,
        }
        body = {"model": "hermes-agent", "messages": messages, "stream": True}
    else:
        url = cfg["opencode_url"].rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": "Bearer " + cfg["opencode_key"],
            "Content-Type": "application/json",
            "User-Agent": "hermes-aichat/1.0",
            "x-opencode-session": "hermes-aichat-web",
        }
        body = {"model": model, "messages": messages, "stream": True}

    try:
        upstream = requests.post(url, json=body, headers=headers, stream=True,
                                 timeout=(10, 900))
    except Exception as e:
        return JsonResponse({"error": "后端连接失败：%s" % e}, status=502)

    if upstream.status_code >= 400:
        detail = upstream.text[:500]
        upstream.close()
        return JsonResponse({"error": "后端返回 %d：%s" % (upstream.status_code, detail)},
                            status=502)

    def stream():
        try:
            for line in upstream.iter_lines(chunk_size=1024):
                if line:
                    yield line + b"\n\n"
                else:
                    yield b": ping\n\n"
        except Exception as e:                       # 上游中断也别让连接悬着
            err = json.dumps({"error": "stream interrupted: %s" % e}, ensure_ascii=False)
            yield ("data: " + err + "\n\n").encode("utf-8")
        finally:
            upstream.close()

    resp = StreamingHttpResponse(stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"                 # 关掉 nginx 缓冲，逐字输出
    return resp


# ─────────────────────────── 文件 ───────────────────────────
@login_required
@require_POST
def api_upload(request):
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "没有收到文件"}, status=400)
    if f.size > MAX_UPLOAD_BYTES:
        return JsonResponse({"error": "文件超过 %d MB 限制" % (MAX_UPLOAD_BYTES // 1048576)},
                            status=413)
    try:
        name = _safe_name(f.name)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    d = _user_dir(request.user)
    dest = os.path.join(d, name)
    if os.path.exists(dest):                         # 同名不覆盖，加时间戳
        stem, ext = os.path.splitext(name)
        name = "%s-%s%s" % (stem, time.strftime("%H%M%S"), ext)
        dest = os.path.join(d, name)
    with open(dest, "wb") as out:
        for chunk in f.chunks():
            out.write(chunk)
    os.chmod(dest, 0o644)
    return JsonResponse({
        "name": name,
        "size": os.path.getsize(dest),
        "agent_path": "%s/u%d/%s" % (AGENT_UPLOAD_ROOT, request.user.id, name),
    })


@login_required
@require_GET
def api_files(request):
    d = _user_dir(request.user)
    items = []
    for n in sorted(os.listdir(d)):
        p = os.path.join(d, n)
        if os.path.isfile(p):
            items.append({
                "name": n,
                "size": os.path.getsize(p),
                "mtime": int(os.path.getmtime(p)),
            })
    items.sort(key=lambda x: -x["mtime"])
    return JsonResponse({"files": items})


@login_required
@require_GET
def api_download(request, name):
    try:
        safe = _safe_name(name)
    except ValueError:
        raise Http404("文件名不合法")
    d = os.path.realpath(_user_dir(request.user))
    path = os.path.realpath(os.path.join(d, safe))
    if not path.startswith(d + os.sep) or not os.path.isfile(path):
        raise Http404("文件不存在")
    return FileResponse(open(path, "rb"), as_attachment=True, filename=safe)
