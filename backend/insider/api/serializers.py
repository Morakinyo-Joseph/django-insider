from rest_framework import serializers
from insider.models import (
    Incidence, Footprint, InsiderSetting,
    InsiderIntegration, InsiderIntegrationKey
)
from insider.settings import settings as insider_settings 


class FootprintListSerializer(serializers.ModelSerializer):
    """Lightweight: For lists (Recent Occurrences, Breadcrumbs)."""
    is_slow = serializers.SerializerMethodField()

    def get_is_slow(self, obj):
        threshold = getattr(insider_settings, 'SLOW_REQUEST_THRESHOLD', None)
        if threshold is None:
            threshold = 500

        if obj.response_time is None:
            return False
        
        try:
            
            return obj.response_time > float(threshold)
        except (TypeError, ValueError):
            return False
        
    
    class Meta:
        model = Footprint
        fields = [
            'id', 'request_id', 'request_method', 'request_path', 'status_code',
            'request_user', 'response_time', 'created_at', 'db_query_count',
            'stack_trace', 'is_slow'
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
            'first_seen', 'last_seen', 'users_affected', 
            'created_at'
        ]

class IncidenceDetailSerializer(serializers.ModelSerializer):
    """For the 'Deep Dive' view."""
    
    users_affected = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Incidence
        fields = '__all__'


class InsiderSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsiderSetting
        fields = [
            'id', 'key', 'value', 'field_type', 
            'description', 'updated_at'
        ]
        read_only_fields = ['key', 'field_type', 'description']



class InsiderIntegrationKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsiderIntegrationKey
        fields = ['id', 'key', 'label', 'value', 'field_type', 'is_required', 'help_text']

    def to_representation(self, instance):
        """
        Security: Mask PASSWORD fields so secrets don't leak to the browser.
        """
        ret = super().to_representation(instance)
        
        if instance.field_type == 'PASSWORD' and instance.value:
            ret['value'] = '********' 
            
        return ret


class InsiderIntegrationSerializer(serializers.ModelSerializer):
    config_keys = InsiderIntegrationKeySerializer(many=True, read_only=True)

    class Meta:
        model = InsiderIntegration
        fields = ['id', 'identifier', 'name', 'description', 'logo_url', 'is_active', 'order', 'config_keys']