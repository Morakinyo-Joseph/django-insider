from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _ 
import json

from insider.models import Footprint 
from insider.settings import settings as insider_settings 


class SlowRequestFilter(admin.SimpleListFilter):
    """
    Filters Footprint records based on the user-configured SLOW_REQUEST_THRESHOLD.
    """
    title = _('Slow Request Status')
    parameter_name = 'is_slow'

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        """
        Provides the options for the filter dropdown.
        """
        # Only show the filter if a threshold is configured
        if insider_settings.SLOW_REQUEST_THRESHOLD is None:
            return []
            
        return [
            ('1', _('Slow (Above Threshold)')),
            ('0', _('Fast (Below Threshold)')),
        ]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """
        Applies the filter to the queryset.
        """

        threshold = insider_settings.SLOW_REQUEST_THRESHOLD

        if threshold is None or self.value() is None:
            return queryset
        
        threshold_ms = float(threshold)

        if self.value() == '1':
            # Filter for requests SLOWER than the threshold (response_time > threshold)
            return queryset.filter(response_time__gt=threshold_ms)
        
        if self.value() == '0':
            # Filter for requests FASTER than or equal to the threshold (response_time <= threshold)
            return queryset.filter(response_time__lte=threshold_ms)
        
        return queryset


@admin.register(Footprint)
class FootprintAdmin(admin.ModelAdmin):
    list_display = (
        "request_id", "request_user", "request_method", "request_path",
        "status_code", "response_time", "db_query_count",
        "is_slow", "created_at"
    )
    
    list_filter = (
        SlowRequestFilter,
        "status_code",
        "request_method",
        "created_at",
    )
    
    search_fields = ("request_path", "request_user", "request_id", "ip_address")
    
    readonly_fields = (
        "request_id", "request_user", "request_method", "request_path",
        "status_code", "response_time", "db_query_count", "created_at",
        "is_slow", "ip_address", "user_agent", 
        "formatted_request_body", "formatted_response_body", "formatted_system_logs"
    )

    # Fieldsets to organize the detail view
    fieldsets = (
        (None, {
            'fields': ('request_id', 'request_user', 'request_method', 'request_path', 'created_at')
        }),
        ("Performance Metrics", {
            'fields': ('status_code', 'response_time', 'db_query_count', 'is_slow')
        }),
        ("Request/Response Data", {
            'classes': ('collapse',),
            'fields': ('formatted_request_body', 'formatted_response_body'),
        }),
        ("System & Logs", {
            'classes': ('collapse',),
            'fields': ('ip_address', 'user_agent', 'formatted_system_logs'),
        }),
    )

    
    @admin.display(description="Slow?", boolean=True)
    def is_slow(self, obj: Footprint) -> bool:
        """
        Returns True if the request response time exceeds the configured threshold.
        """
        threshold = insider_settings.SLOW_REQUEST_THRESHOLD
        
        if threshold is None:
            return False
            
        return obj.response_time > float(threshold)
    

    @admin.display(description="Request Body", empty_value="N/A")
    def formatted_request_body(self, obj: Footprint) -> str:
        """
        Renders the JSON request body in a readable, pre-formatted block.
        """

        if obj.request_body and isinstance(obj.request_body, dict):
            html = json.dumps(obj.request_body, indent=4)
            
            return mark_safe(f"<pre style='background: #f4f4f4; padding: 10px; border: 1px solid #ddd; white-space: pre-wrap;'>{html}</pre>")
        
        return obj.request_body or ""

    

    @admin.display(description="Response Body", empty_value="N/A")
    def formatted_response_body(self, obj: Footprint) -> str:
        """
        Renders the JSON response body in a readable, pre-formatted block.
        """

        if obj.response_body and isinstance(obj.response_body, dict):
            html = json.dumps(obj.response_body, indent=4)
            return mark_safe(f"<pre style='background: #f4f4f4; padding: 10px; border: 1px solid #ddd; white-space: pre-wrap;'>{html}</pre>")
        
        elif obj.response_body:
             # Handle non-JSON (HTML/text) responses
            return mark_safe(f"<pre style='background: #f4f4f4; padding: 10px; border: 1px solid #ddd; white-space: pre-wrap;'>{obj.response_body}</pre>")

        return obj.response_body or ""


    @admin.display(description="System Logs", empty_value="No Logs Captured")
    def formatted_system_logs(self, obj: Footprint) -> str:
        """
        Renders captured system logs as a list, highlighting errors.
        """

        if obj.system_logs and isinstance(obj.system_logs, list):
            html_list = []

            for log_entry in obj.system_logs:
                style = ""

                # Simple check for log level for visual cue
                entry_upper = log_entry.upper()

                if entry_upper.startswith("ERROR"):
                    style = "color: red; font-weight: bold;"

                elif entry_upper.startswith("WARNING"):
                    style = "color: orange;"
                
                html_list.append(f"<li style='{style}'>{log_entry}</li>")
            
            return mark_safe(f"<ul style='list-style: none; padding: 0;'>{''.join(html_list)}</ul>")
        
        return obj.system_logs or ""