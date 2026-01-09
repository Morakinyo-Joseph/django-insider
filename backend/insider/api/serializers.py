from rest_framework import serializers
from insider.models import Incidence, Footprint


class FootprintListSerializer(serializers.ModelSerializer):
    """Lightweight: For lists (Recent Occurrences, Breadcrumbs)."""

    class Meta:
        model = Footprint
        fields = [
            'id', 'request_id', 'request_method', 'request_path', 'status_code',
            'request_user', 'response_time', 'created_at', 'db_query_count',
            'stack_trace'
        ]

class FootprintDetailSerializer(serializers.ModelSerializer):
    """Heavyweight: For the 'Forensics' Lab. Includes full bodies and logs."""

    class Meta:
        model = Footprint
        fields = '__all__'


class IncidenceListSerializer(serializers.ModelSerializer):
    """
    For the 'Incidence' table.
    'users_affected' will be injected by the View's annotation (SQL count).
    """

    users_affected = serializers.IntegerField(read_only=True)

    class Meta:
        model = Incidence
        fields = [
            'id', 'title', 'status', 'occurrence_count', 
            'first_seen', 'last_seen', 'users_affected'
        ]

class IncidenceDetailSerializer(serializers.ModelSerializer):
    """For the 'Deep Dive' view."""
    
    users_affected = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Incidence
        fields = '__all__'