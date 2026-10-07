"""全站登录策略：默认查询（GET/HEAD/OPTIONS）放行，
所有写操作（POST/PUT/PATCH/DELETE）必须登录。"""
from django.http import JsonResponse
from django.shortcuts import redirect

# 放行的路径前缀（登录、登出、静态资源、admin 由其自身处理）
EXEMPT_PREFIXES = (
    '/accounts/login',
    '/accounts/logout',
    '/static/',
    '/favicon.ico',
)

WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        method = request.method.upper()
        path = request.path

        exempt = any(path.startswith(p) for p in EXEMPT_PREFIXES)

        # admin 站点保持其原有登录机制
        if path.startswith('/admin'):
            return self.get_response(request)

        if not exempt and method in WRITE_METHODS and not request.user.is_authenticated:
            # AJAX / API 请求返回 401，前端据此跳转登录
            if (request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    or 'application/json' in request.headers.get('Accept', '')
                    or path.startswith('/classroom/api')
                    or request.content_type == 'application/json'):
                return JsonResponse(
                    {'detail': '需要登录后才能进行该操作', 'login_required': True},
                    status=401)
            return redirect('/accounts/login/?next=' + path)

        return self.get_response(request)
