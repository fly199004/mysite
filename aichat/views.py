# -*- coding: utf-8 -*-
"""
飞云 AI 对话 · 后端
===================
- 会话与消息落库（按登录用户隔离），刷新/换设备都能接着聊
- 两种后端：hermes（容器内 Agent，带工具）/ direct（OpenCode Go 直连，可切模型）
- SSE 流式转发 + 结束后写库（客户端中断也会保存已生成的部分）

环境依赖：Django >= 3.2、requests
"""
import json
import mimetypes
import os
import re
import time

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import (FileResponse, Http404, HttpResponseBadRequest,
                         JsonResponse, StreamingHttpResponse)
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Conversation, Message

# ───────────────────────── 配置 ─────────────────────────
DEFAULT_HERMES_URL = 'http://hermes:8642/v1'
DEFAULT_DIRECT_URL = 'https://opencode.ai/zen/go/v1'
DEFAULT_AGENT_MOUNT = '/mnt/uploads'          # hermes 容器里看到的附件目录
MODEL_CACHE_TTL = 600
_BLOCKED_MODELS = {'beam-free', 'cat-jam-free', 'step-5-preview-free', 'test'}
_model_cache = {'at': 0, 'data': []}

SYSTEM_PROMPT = (
    '你是「飞云 AI」，刘飞生老师个人网站里的 AI 助手。'
    '回答用简体中文，简洁准确；涉及代码请用 Markdown 代码块并标注语言；'
    '不确定的内容直接说明不确定，不要编造。'
)


def _cfg():
    """读取 /app/aichat_config.json；兼容嵌套与扁平两种写法，缺项回落环境变量/默认值。"""
    raw = {}
    path = getattr(settings, 'AICHAT_CONFIG_PATH', '/app/aichat_config.json')
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            raw = json.load(fh)
    except Exception:
        raw = {}

    def pick(*keys, **kw):
        default = kw.get('default', '')
        for k in keys:
            cur = raw
            ok = True
            for part in k.split('.'):
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    ok = False
                    break
            if ok and isinstance(cur, str) and cur.strip():
                return cur.strip()
        for k in keys:
            env = os.environ.get(k.split('.')[-1].upper())
            if env:
                return env.strip()
        return default

    hermes_url = pick('hermes_url', 'hermes.url', 'backends.hermes.url', default=DEFAULT_HERMES_URL).rstrip('/')
    direct_url = pick('direct_url', 'direct.url', 'backends.direct.url', default=DEFAULT_DIRECT_URL).rstrip('/')
    return {
        'hermes': {
            'url': hermes_url + '/chat/completions',
            'key': pick('hermes_key', 'hermes.key', 'backends.hermes.key', default=''),
        },
        'direct': {
            'url': direct_url + '/chat/completions',
            'models_url': direct_url + '/models',
            'key': pick('direct_key', 'direct.key', 'backends.direct.key',
                        'opencode_go_api_key', default=os.environ.get('OPENCODE_GO_API_KEY', '')),
        },
        'agent_mount': pick('agent_mount', default=DEFAULT_AGENT_MOUNT).rstrip('/'),
        'upload_root': getattr(settings, 'AICHAT_UPLOAD_ROOT', '/app/aichat_uploads'),
    }


def _user_dir(user):
    root = _cfg()['upload_root']
    path = os.path.join(root, 'u%s' % user.id)
    os.makedirs(path, exist_ok=True)
    return path


def _agent_path(user, name):
    return '%s/u%s/%s' % (_cfg()['agent_mount'], user.id, name)


# ───────────────────────── 工具函数 ─────────────────────────
def _json_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return {}


def _sse(payload):
    return 'data: %s\n\n' % json.dumps(payload, ensure_ascii=False)


def _short_title(text):
    text = re.sub(r'\s+', ' ', (text or '')).strip()
    return text[:24] + ('…' if len(text) > 24 else '') or '新对话'


def _group_of(model_id):
    mid = (model_id or '').lower()
    table = (
        (('gpt', 'o1', 'o3', 'o4'), 'OpenAI'),
        (('claude',), 'Anthropic'),
        (('gemini',), 'Google'),
        (('deepseek',), 'DeepSeek'),
        (('glm', 'chatglm'), '智谱 GLM'),
        (('kimi', 'moonshot'), '月之暗面'),
        (('qwen', 'qwq'), '通义千问'),
        (('grok',), 'xAI'),
        (('llama',), 'Meta'),
        (('minimax', 'abab'), 'MiniMax'),
        (('doubao', 'seed'), '豆包'),
        (('mistral', 'mixtral', 'devstral'), 'Mistral'),
    )
    for keys, name in table:
        if any(mid.startswith(k) or ('-' + k) in mid for k in keys):
            return name
    return '其他模型'


# ───────────────────────── 页面 ─────────────────────────
@login_required
@ensure_csrf_cookie
def page(request):
    return render(request, 'aichat/index.html')


# ───────────────────────── 初始化 ─────────────────────────
@login_required
@require_GET
def bootstrap(request):
    user = request.user
    name = (user.get_full_name() or '').strip() or user.username
    role = '教师' if user.is_staff else '已登录'
    return JsonResponse({
        'user': {
            'id': user.id,
            'name': name,
            'initial': (name or 'U')[0].upper() if name else 'U',
            'role': role,
        },
        'csrf': request.META.get('CSRF_COOKIE', ''),
        'backends': ['hermes', 'direct'],
    })


@login_required
@require_GET
def models(request):
    """直连模式的可用模型清单，10 分钟缓存；上游挂了就返回兜底列表。"""
    now = time.time()
    if _model_cache['data'] and now - _model_cache['at'] < MODEL_CACHE_TTL:
        return JsonResponse({'models': _model_cache['data'], 'cached': True})

    cfg = _cfg()['direct']
    items = []
    try:
        headers = {'Authorization': 'Bearer ' + cfg['key']} if cfg['key'] else {}
        headers['x-opencode-session'] = 'liufeisheng-site'
        resp = requests.get(cfg['models_url'], headers=headers, timeout=12)
        resp.raise_for_status()
        data = resp.json().get('data') or resp.json().get('models') or []
        for m in data:
            mid = m.get('id') if isinstance(m, dict) else str(m)
            if not mid or mid in _BLOCKED_MODELS:
                continue
            items.append({'id': mid, 'label': mid, 'group': _group_of(mid)})
    except Exception:
        items = []

    if not items:
        fallback = ['deepseek-v4.1-flash', 'deepseek-v4-flash', 'glm-4.7-flash',
                    'gemini-3.6-flash', 'kimi-k2', 'gpt-5.2-mini']
        items = [{'id': m, 'label': m, 'group': _group_of(m)} for m in fallback]

    order = ['DeepSeek', 'OpenAI', 'Anthropic', 'Google', '智谱 GLM', '月之暗面',
             '通义千问', 'xAI', '豆包', 'MiniMax', 'Mistral', 'Meta', '其他模型']
    items.sort(key=lambda x: (order.index(x['group']) if x['group'] in order else 99, x['id']))
    _model_cache['at'], _model_cache['data'] = now, items
    return JsonResponse({'models': items})


# ───────────────────────── 会话 ─────────────────────────
@login_required
@require_http_methods(['GET', 'POST'])
def conversations(request):
    if request.method == 'GET':
        qs = (Conversation.objects
              .filter(user=request.user, archived=False)
              .order_by('-pinned', '-updated_at')[:200])
        return JsonResponse({'conversations': [c.as_dict() for c in qs]})

    data = _json_body(request)
    conv = Conversation.objects.create(
        user=request.user,
        title=(data.get('title') or '')[:120],
        backend=data.get('backend') or 'hermes',
        model=(data.get('model') or '')[:80],
    )
    return JsonResponse({'conversation': conv.as_dict()}, status=201)


def _get_conv(request, cid):
    try:
        return Conversation.objects.get(id=cid, user=request.user)
    except Conversation.DoesNotExist:
        raise Http404('会话不存在')


@login_required
@require_http_methods(['GET', 'PATCH', 'DELETE'])
def conversation_detail(request, cid):
    conv = _get_conv(request, cid)
    if request.method == 'GET':
        return JsonResponse({'conversation': conv.as_dict()})

    if request.method == 'PATCH':
        data = _json_body(request)
        if 'title' in data:
            conv.title = (data.get('title') or '').strip()[:120] or conv.title
        if 'pinned' in data:
            conv.pinned = bool(data.get('pinned'))
        if 'archived' in data:
            conv.archived = bool(data.get('archived'))
        if 'model' in data:
            conv.model = (data.get('model') or '')[:80]
        if 'backend' in data:
            conv.backend = (data.get('backend') or conv.backend)[:16]
        conv.save()
        return JsonResponse({'conversation': conv.as_dict()})

    conv.delete()
    return JsonResponse({'ok': True})


@login_required
@require_GET
def conversation_messages(request, cid):
    conv = _get_conv(request, cid)
    msgs = conv.messages.all().order_by('id')
    return JsonResponse({
        'conversation': conv.as_dict(),
        'messages': [m.as_dict() for m in msgs],
    })


@login_required
@require_http_methods(['DELETE'])
def message_detail(request, cid, mid):
    conv = _get_conv(request, cid)
    deleted, _ = Message.objects.filter(id=mid, conversation=conv).delete()
    return JsonResponse({'ok': bool(deleted)})


# ───────────────────────── 对话主流程 ─────────────────────────
@login_required
@require_POST
def chat(request):
    data = _json_body(request)
    text = (data.get('message') or '').strip()
    if not text:
        return HttpResponseBadRequest('message 不能为空')

    backend = 'direct' if data.get('backend') == 'direct' else 'hermes'
    model = (data.get('model') or '').strip() if backend == 'direct' else ''
    atts = [a for a in (data.get('attachments') or []) if isinstance(a, dict) and a.get('name')]

    # 定位/新建会话
    conv = None
    if data.get('conversation_id'):
        try:
            conv = Conversation.objects.get(id=int(data['conversation_id']), user=request.user)
            if not conv.title:
                conv.title = _short_title(text)
        except (Conversation.DoesNotExist, ValueError, TypeError):
            conv = None
    if conv is None:
        conv = Conversation.objects.create(
            user=request.user, title=_short_title(text),
            backend=backend, model=model,
        )

    conv.backend, conv.model = backend, model
    conv.save(update_fields=['backend', 'model'])

    # 「重新生成」：把上一轮用户提问及其后的回答一起删掉，再用同样的提问重发
    if data.get('regenerate'):
        last_user = conv.messages.filter(role='user').order_by('-id').first()
        if last_user:
            conv.messages.filter(id__gte=last_user.id).delete()

    user_msg = Message(conversation=conv, role='user', content=text,
                       backend=backend, model=model)
    user_msg.attachments = atts
    user_msg.save()

    # 组装上游 messages（取最近 40 条，避免长会话越聊越慢/越贵）
    recent = list(conv.messages.order_by('-id')[:40])
    history = list(reversed(recent))
    payload_msgs = []
    if backend == 'direct':
        payload_msgs.append({'role': 'system', 'content': SYSTEM_PROMPT})
    for m in history:
        if m.role not in ('user', 'assistant'):
            continue
        content = m.content or ''
        if m.id == user_msg.id and atts and backend == 'hermes':
            lines = '\n'.join('- %s（%s）' % (a.get('name'), a.get('agent_path') or '')
                              for a in atts)
            content += ('\n\n[附件] 用户上传了以下文件，可直接用文件工具读取；'
                        '如生成了新文件，请写入同一目录：\n' + lines)
        payload_msgs.append({'role': m.role, 'content': content})

    cfg = _cfg()[backend]
    upstream = {'model': model or 'hermes-agent', 'messages': payload_msgs,
                'stream': True, 'temperature': 0.7}
    headers = {'Content-Type': 'application/json', 'Accept': 'text/event-stream'}
    if cfg['key']:
        headers['Authorization'] = 'Bearer ' + cfg['key']
    if backend == 'hermes':
        headers['x-opencode-session'] = 'hermes-nas-opencode-go'
        headers['X-Hermes-Session-Key'] = 'aichat:user:%s:conv:%s' % (request.user.id, conv.id)
    else:
        # OpenCode Go 强制要求 x-opencode-session，缺了直接 400 MissingSessionID
        headers['x-opencode-session'] = 'aichat-site-u%s-conv%s' % (request.user.id, conv.id)

    conv_id, conv_title = conv.id, conv.title

    def gen():
        acc, err_text = [], ''
        try:
            yield _sse({'conversation_id': conv_id, 'title': conv_title})
            resp = requests.post(cfg['url'], json=upstream, headers=headers,
                                 stream=True, timeout=(15, 600))
            if resp.status_code >= 400:
                body = ''
                try:
                    body = resp.text[:400]
                except Exception:
                    pass
                raise RuntimeError('上游 %s 返回 %s %s' % (backend, resp.status_code, body))

            for raw in resp.iter_lines(decode_unicode=True):
                if raw is None:
                    continue
                line = raw.strip()
                if not line or line.startswith(':'):
                    continue
                if not line.startswith('data:'):
                    continue
                chunk = line[5:].strip()
                if chunk == '[DONE]':
                    break
                try:
                    obj = json.loads(chunk)
                except Exception:
                    continue
                delta = ''
                choices = obj.get('choices') or []
                if choices:
                    d = choices[0].get('delta') or {}
                    delta = d.get('content') or ''
                    if not delta:
                        delta = (choices[0].get('message') or {}).get('content') or ''
                elif isinstance(obj.get('delta'), str):
                    delta = obj['delta']
                elif isinstance(obj.get('content'), str) and obj.get('type') in (None, 'delta', 'text'):
                    delta = obj['content']
                if delta:
                    acc.append(delta)
                    yield _sse({'delta': delta})
            yield _sse({'done': True})
        except GeneratorExit:
            err_text = ''
            raise
        except Exception as exc:
            err_text = str(exc)[:500]
            try:
                yield _sse({'error': err_text})
            except Exception:
                pass
        finally:
            content = ''.join(acc)
            try:
                Message.objects.create(
                    conversation_id=conv_id, role='assistant', content=content,
                    backend=backend, model=model, error=bool(err_text) and not content,
                )
                Conversation.objects.filter(id=conv_id).update(updated_at=timezone.now())
            except Exception:
                pass

    resp = StreamingHttpResponse(gen(), content_type='text/event-stream; charset=utf-8')
    resp['Cache-Control'] = 'no-cache, no-transform'
    resp['X-Accel-Buffering'] = 'no'
    resp['Connection'] = 'keep-alive'
    return resp


# ───────────────────────── 文件 ─────────────────────────
NAME_RE = re.compile(r'^[\w\u4e00-\u9fff][\w\u4e00-\u9fff .\-()\[\]]{0,119}$', re.UNICODE)
MAX_UPLOAD = 50 * 1024 * 1024


@login_required
@require_POST
def upload(request):
    up = request.FILES.get('file')
    if not up:
        return HttpResponseBadRequest('缺少 file 字段')
    if up.size > MAX_UPLOAD:
        return HttpResponseBadRequest('文件超过 50MB')

    name = os.path.basename(up.name or 'file')
    if not NAME_RE.match(name):
        return HttpResponseBadRequest('文件名含不允许的字符')

    folder = _user_dir(request.user)
    target = os.path.join(folder, name)
    if os.path.exists(target):
        stem, ext = os.path.splitext(name)
        name = '%s_%s%s' % (stem, time.strftime('%H%M%S'), ext)
        target = os.path.join(folder, name)

    with open(target, 'wb') as fh:
        for chunk in up.chunks():
            fh.write(chunk)
    try:
        os.chmod(target, 0o666)
    except Exception:
        pass

    return JsonResponse({'name': name, 'size': up.size,
                         'agent_path': _agent_path(request.user, name)})


@login_required
@require_GET
def files(request):
    folder = _user_dir(request.user)
    out = []
    for name in sorted(os.listdir(folder)):
        full = os.path.join(folder, name)
        if not os.path.isfile(full) or name.startswith('.'):
            continue
        st = os.stat(full)
        out.append({'name': name, 'size': st.st_size,
                    'mtime': int(st.st_mtime),
                    'agent_path': _agent_path(request.user, name)})
    out.sort(key=lambda x: -x['mtime'])
    return JsonResponse({'files': out})


@login_required
@require_GET
def file_download(request, name):
    folder = os.path.realpath(_user_dir(request.user))
    full = os.path.realpath(os.path.join(folder, name))
    if not full.startswith(folder + os.sep) or not os.path.isfile(full):
        raise Http404('文件不存在')
    ctype, _ = mimetypes.guess_type(full)
    return FileResponse(open(full, 'rb'), as_attachment=True,
                        filename=os.path.basename(full),
                        content_type=ctype or 'application/octet-stream')
