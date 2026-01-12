from django.urls import path, include, re_path
from . import views

urlpatterns = [
    # Forward API traffic to the EXISTING api/urls.py
    path('api/', include('insider.api.urls')),

    # Catch everything else and serve the React App
    re_path(r'^.*$', views.serve_dashboard, name='insider_dashboard'),
]