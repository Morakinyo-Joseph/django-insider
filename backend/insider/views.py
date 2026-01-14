import os
import mimetypes
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def serve_dashboard(request, resource=""):
    """
    Serves the React frontend AND its static assets directly from the package.
    """
    current_dir = os.path.dirname(__file__)
    
    if resource.startswith("assets/"):
        file_path = os.path.join(current_dir, 'static', 'insider', resource)
        
        if os.path.exists(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            
            with open(file_path, 'rb') as f:
                return HttpResponse(f.read(), content_type=content_type)
        else:
            raise Http404(f"Asset not found: {resource}")

    index_path = os.path.join(current_dir, 'static', 'insider', 'index.html')

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())
    except FileNotFoundError:
        return HttpResponse(
            "Insider Error: index.html not found. Did you run 'npm run build'?", 
            status=501
        )