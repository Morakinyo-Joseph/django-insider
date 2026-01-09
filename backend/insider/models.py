from django.db import models


class Incidence(models.Model):
    """
    Represents a unique group of errors (aggregated by fingerprint).
    """

    STATUS_CHOICES = (
        ("OPEN", "Open"),
        ("RESOLVED", "Resolved"),
        ("IGNORED", "Ignored"),
    )

    fingerprint = models.CharField(
        max_length=64, 
        unique=True,
        db_index=True
    )
    title = models.CharField(max_length=255)

    occurrence_count = models.PositiveIntegerField(default=1)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN"
    )

    last_notified = models.DateTimeField(
        auto_now_add=True, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"{self.title} ({self.occurrence_count})"

    
class Footprint(models.Model):
    """
    Stores a detailed record of each HTTP request/response cycle captured by
    the Insider logging middleware.

    This model helps developers track API usage, debug incidences, analyze
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

    incidence = models.ForeignKey(
        Incidence, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
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

    exception_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    stack_trace = models.JSONField(null=True, blank=True
                                   )

    class Meta:
        verbose_name = "Footprint"
        verbose_name_plural = "Footprints"


    def __str__(self):
        return f"[{self.request_id}] {self.request_method.upper()} {self.request_path} -> {self.status_code}"    


