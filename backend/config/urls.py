from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import Http404, HttpResponse
from django.urls import include, path, re_path
from .views import _500, _200
def serve_frontend_app(request, resource=""):
    """
    Serves the React app from 'backend/insider/static/insider/index.html'.
    This mimics the logic from your reference project.
    """
    try:
        # Note: We look for "insider/index.html" because Vite builds to that static folder
        with staticfiles_storage.open("insider/index.html") as index_file:
            return HttpResponse(index_file.read(), content_type="text/html")
    except FileNotFoundError:
        return HttpResponse(
            """
            <h1>Frontend Not Found</h1>
            <p>Please run <code>npm run build</code> in the <code>frontend/</code> directory.</p>
            """,
            status=501
        )

urlpatterns = [
    path("admin/", admin.site.urls),

    # 1. API Routes
    # This points directly to your existing 'insider/api/urls.py'
    # URL result: http://localhost:8000/insider/api/incidences/
    path("insider/api/", include("insider.api.urls")),

    # 2. Frontend Routes
    # We use re_path here so that deep links (e.g. /insider/incidences/5) 
    # don't 404 but instead load React.
    # URL result: http://localhost:8000/insider/
    re_path(r"^insider/(?P<resource>.*)$", serve_frontend_app, name="insider-frontend"),

    path("500", _500.as_view(), name="500 request"),
    path("200", _200.as_view(), name="200 request"),
    
]