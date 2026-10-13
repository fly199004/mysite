from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("go/<str:course_id>/", views.course_go, name="course_go"),
    path("<str:course_id>/", views.course_detail, name="course_detail"),
]
