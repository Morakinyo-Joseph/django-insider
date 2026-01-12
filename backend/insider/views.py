import os
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse

@ensure_csrf_cookie
def serve_dashboard(request, resource=""):
    """
    Serves the React frontend. 
    Located inside the package so the user doesn't have to write this.
    """

    # structure is: insider/views.py -> insider/static/insider/index.html
    current_dir = os.path.dirname(__file__)
    index_path = os.path.join(current_dir, 'static', 'insider', 'index.html')

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())
    except FileNotFoundError:
        return HttpResponse(
            "Insider Error: index.html not found. Did you run 'npm run build'?", 
            status=501
        )