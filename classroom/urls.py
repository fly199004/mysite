"""classroom 应用路由（挂在 /classroom/ 下）。"""
from django.urls import path

from . import views

app_name = "classroom"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/health", views.health, name="health"),
    path("api/classes", views.list_classes, name="list"),
    path("api/classes/create", views.create_class, name="create"),
    path("api/meta/current", views.current, name="current"),
    path("api/replace-all", views.replace_all, name="replace_all"),
    path("api/classes/<str:class_id>/rename", views.rename_class, name="rename"),
    path("api/classes/<str:class_id>/state", views.state_class, name="state"),
    path("api/classes/<str:class_id>/delete", views.delete_class, name="delete"),
]
