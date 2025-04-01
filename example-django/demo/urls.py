from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('trigger-error/', views.trigger_error, name='trigger-error'),
    path('trigger-warning/', views.trigger_warning, name='trigger-warning'),
] 