from django.contrib import admin
from django.urls import include, path
from .views import _500, _200

urlpatterns = [
    path("admin/", admin.site.urls),
    path('insider/', include('insider.urls')),

    path("500", _500.as_view(), name="500 request"),
    path("200", _200.as_view(), name="200 request"),
    
]