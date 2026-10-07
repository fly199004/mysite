"""accounts 应用路由。"""
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password/', views.password_change, name='password_change'),
    path('password/done/', views.password_change_done, name='password_change_done'),
    path('api/me/', views.api_me, name='api_me'),
    path('manage/', views.user_list, name='user_list'),
    path('manage/new/', views.user_create, name='user_create'),
    path('manage/<int:user_id>/toggle/', views.user_toggle_active, name='user_toggle'),
    path('manage/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('manage/<int:user_id>/reset-password/', views.user_reset_password,
         name='user_reset_password'),
]
