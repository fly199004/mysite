from django.shortcuts import render
# urls.py
from django.urls import path
from . import views

# Create your views here.

def index(request):
    return render(request, 'index.html')


urlpatterns = [
    path('', views.index, name='index'),
]
