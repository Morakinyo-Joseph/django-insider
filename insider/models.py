from django.db import models


class Footprint(models.Model):
    """
    Stores a detailed record of each HTTP request/response cycle captured by
    the Insider logging middleware.

    This model helps developers track API usage, debug issues, analyze
    performance, and monitor system behaviour. Each entry contains information
    about the incoming request (path, method, user, body, metadata), the
    generated response (body, status code, duration), and optional system logs
    or database query counts collected during processing.

    A `Footprint` instance essentially represents a complete snapshot of how
    Django handled a specific request.
    """

    METHOD_CHOICES = (
        ("get", "Get"),
        ("post", "Post"),
        ("put", "Put"),
        ("patch", "Patch"),
        ("delete", "Delete")
    )

    request_id = models.CharField(
        max_length=36,
        unique=True,
        editable=False,
        help_text="Unique identifier for the request/response cycle.",
        null=True,
        blank=True
    )

    request_user = models.CharField(
        max_length=50, 
        default="anonymous",
        help_text="Authenticated user ID or 'anonymous'."
    )
    request_path = models.CharField(max_length=255)
    request_body = models.JSONField(
        null=True, 
        blank=True,
        help_text="Parsed request body (e.g., POST/JSON data)."
    )
    request_method = models.CharField(
        max_length=20, 
        choices=METHOD_CHOICES, 
        blank=True, 
        null=True
    )
    
    response_body = models.JSONField(null=True, blank=True)
    response_time = models.FloatField(
        default=0.0, 
        help_text="Total request to response duration in milliseconds (ms)"
    )
    status_code = models.IntegerField(default=200)
    system_logs = models.JSONField(
        null=True, 
        blank=True,
        help_text="Captured system logs (list of strings)."

    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=512, null=True, blank=True)
    
    db_query_count = models.IntegerField(
        default=0, 
        help_text="Total database connection queries."
    )
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = "Footprint"
        verbose_name_plural = "Footprints"


    def __str__(self):
        return f"[{self.request_id}] {self.request_method.upper()} {self.request_path} -> {self.status_code}"    


