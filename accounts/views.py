"""账号体系视图：登录、登出、改密、用户增删改查（管理员）。"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, AdminPasswordChangeForm, SetPasswordForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import CreateUserForm


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def admin_required(view_func):
    """管理员（staff/superuser）可用；已登录但非管理员 -> 403；未登录 -> 登录页。"""
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path(), login_url='/accounts/login/')
        if not is_admin(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


# ---------------- 登录 / 登出 ----------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect(request.GET.get('next') or '/')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            nxt = request.GET.get('next') or request.POST.get('next') or '/'
            return redirect(nxt)
    else:
        form = AuthenticationForm(request)
    return render(request, 'accounts/login.html', {
        'form': form,
        'next': request.GET.get('next', '/'),
    })


def logout_view(request):
    logout(request)
    messages.info(request, '您已安全退出。')
    return redirect('/')


# ---------------- 修改自己的密码 ----------------
@login_required
def password_change(request):
    if request.method == 'POST':
        from django.contrib.auth.forms import PasswordChangeForm
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, '密码修改成功。')
            return redirect('accounts:password_change_done')
    else:
        from django.contrib.auth.forms import PasswordChangeForm
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})


def password_change_done(request):
    return render(request, 'accounts/password_change_done.html')


# ---------------- 登录态查询（GET 公开） ----------------
def api_me(request):
    """供前端工具判断是否已登录；GET 免登录。"""
    u = request.user
    return JsonResponse({
        'authenticated': bool(u.is_authenticated),
        'username': u.username if u.is_authenticated else '',
        'is_staff': bool(u.is_authenticated and (u.is_staff or u.is_superuser)),
    })


# ---------------- 管理员：用户列表 / 新建 / 启停 / 删除 / 重置密码 ----------------
@admin_required
def user_list(request):
    users = User.objects.all().order_by('-is_superuser', '-is_staff', 'username')
    return render(request, 'accounts/user_list.html', {'users': users})


@admin_required
def user_create(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            form.save_m2m()
            messages.success(request, f'账号 “{user.username}” 创建成功。')
            return redirect('accounts:user_list')
    else:
        form = CreateUserForm()
    return render(request, 'accounts/user_form.html', {
        'form': form, 'title': '新建普通账号'})


@admin_required
def user_toggle_active(request, user_id):
    u = User.objects.filter(pk=user_id).first()
    if not u:
        messages.error(request, '账号不存在。')
        return redirect('accounts:user_list')
    if u == request.user:
        messages.error(request, '不能停用当前登录账号。')
        return redirect('accounts:user_list')
    u.is_active = not u.is_active
    u.save(update_fields=['is_active'])
    messages.success(request, f'账号 “{u.username}” 已'
                              + ('启用' if u.is_active else '停用') + '。')
    return redirect('accounts:user_list')


@admin_required
def user_delete(request, user_id):
    u = User.objects.filter(pk=user_id).first()
    if not u:
        messages.error(request, '账号不存在。')
        return redirect('accounts:user_list')
    if u.is_superuser:
        messages.error(request, '不能删除超级管理员账号。')
        return redirect('accounts:user_list')
    if u == request.user:
        messages.error(request, '不能删除当前登录账号。')
        return redirect('accounts:user_list')
    name = u.username
    u.delete()
    messages.success(request, f'账号 “{name}” 已删除。')
    return redirect('accounts:user_list')


@admin_required
def user_reset_password(request, user_id):
    u = User.objects.filter(pk=user_id).first()
    if not u:
        messages.error(request, '账号不存在。')
        return redirect('accounts:user_list')
    if request.method == 'POST':
        form = SetPasswordForm(u, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'已为 “{u.username}” 重置密码。')
            return redirect('accounts:user_list')
    else:
        form = SetPasswordForm(u)
    return render(request, 'accounts/user_reset_password.html', {
        'form': form, 'target_user': u})
