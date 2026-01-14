from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('api/', include('insider.api.urls')),

    re_path(r'^(?P<resource>.*)$', views.serve_dashboard, name='insider_dashboard'),
]