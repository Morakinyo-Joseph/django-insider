import django_filters
from django.db.models import Q, TextField
from django.contrib.auth import get_user_model
from django.db.models.functions import Cast
from insider.models import Footprint

class FootprintFilter(django_filters.FilterSet):
    """
    Advanced filtering for the Footprint (Detective/Forensics) View.
    """
    # 1. User & Source Context
    request_user = django_filters.CharFilter(method='filter_user_identifier')
    ip_address = django_filters.CharFilter(lookup_expr='exact')
    user_agent = django_filters.CharFilter(lookup_expr='icontains')

    # 2. Technical Scope
    # Allows selecting multiple methods (e.g., GET and POST)
    request_method = django_filters.MultipleChoiceFilter(choices=Footprint.METHOD_CHOICES)
    request_path = django_filters.CharFilter(lookup_expr='icontains')
    exception_name = django_filters.CharFilter(lookup_expr='icontains')
    
    # Allows comma-separated status codes (e.g., ?status_code__in=500,502,504)
    status_code__in = django_filters.BaseInFilter(field_name='status_code', lookup_expr='in')

    # 3. Performance & Bottlenecks
    min_response_time = django_filters.NumberFilter(field_name='response_time', lookup_expr='gte')
    min_db_queries = django_filters.NumberFilter(field_name='db_query_count', lookup_expr='gte')

    # Time ranges for correlation
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    # 4. Deep Content Search (The 'Needle in a Haystack')
    global_search = django_filters.CharFilter(method='filter_global_search')

    class Meta:
        model = Footprint
        fields = [
            'request_user', 'ip_address', 'request_method', 
            'request_path', 'exception_name'
        ]

    def filter_user_identifier(self, queryset, name, value):
        """
        Allows searching by User ID (direct match) OR Email/Username (resolved to ID).
        """
        User = get_user_model()
        # Resolve email/username to IDs
        matching_users = User.objects.filter(
            Q(email__icontains=value) | Q(username__icontains=value)
        ).values_list('id', flat=True)
        
        return queryset.filter(
            Q(request_user__icontains=value) | 
            Q(request_user__in=[str(uid) for uid in matching_users])
        )

    def filter_global_search(self, queryset, name, value):
        """
        Scans all JSON and text payloads simultaneously for a specific string.
        In PostgreSQL, `icontains` on JSONFields works seamlessly.
        """
        return queryset.annotate(
            search_request_body=Cast('request_body', TextField()),
            search_response_body=Cast('response_body', TextField()),
            search_stack_trace=Cast('stack_trace', TextField()),
            search_system_logs=Cast('system_logs', TextField()),
        ).filter(
            Q(search_request_body__icontains=value) | 
            Q(search_response_body__icontains=value) | 
            Q(search_stack_trace__icontains=value) |
            Q(search_system_logs__icontains=value) |
            Q(exception_name__icontains=value)
        )