from datetime import timedelta
from django.db.models import Count, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.mixins import UpdateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from insider.models import Incidence, Footprint, InsiderSetting
from insider.settings import DEFAULTS, reload_settings
from .serializers import (
    IncidenceListSerializer, IncidenceDetailSerializer,
    FootprintListSerializer, FootprintDetailSerializer,
    InsiderSettingSerializer
)


class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IncidenceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Powers the 'Incidence' and 'Deep Dive' rooms.
    """
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = Incidence.objects.annotate(
            users_affected=Count('footprint__request_user', distinct=True)
        ).order_by('-last_seen')

        filter_type = self.request.query_params.get("filter")

        # filter by incidences created in the last hour
        if filter_type == "new":
            one_hour_ago = timezone.now() - timedelta(hours=1)
            qs = qs.filter(created_at__gte=one_hour_ago)

        # filter by incidences with high occurence counts.
        if filter_type == "regressions":
            qs = qs.filter(status='OPEN', occurrence_count__gt=1)
        
        return qs 

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IncidenceDetailSerializer
        return IncidenceListSerializer
    
    @action(detail=False, methods=['post'])
    def bulk_resolve(self, request):
        """
        Receives: { "ids": [1, 2, 5] }
        Action: Sets status='RESOLVED' for all those IDs.
        """

        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No IDs provided"}, status=400)
        
        count = Incidence.objects.filter(id__in=ids).update(status='RESOLVED')
        return Response({"message": f"Resolved {count} incidence"}, status=200)
    

    @action(detail=False, methods=['post'])
    def bulk_ignore(self, request):
        """
        Receives: { "ids": [1, 2, 5] }
        Action: Sets status='IGNORED' for all those IDs.
        """

        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No IDs provided"}, status=400)
        
        count = Incidence.objects.filter(id__in=ids).update(status='IGNORED')
        return Response({"message": f"Ignored {count} incidence"}, status=200)


    @action(detail=True, methods=['get'])
    def footprints(self, request, pk=None):
        """
        Returns the 20 most recent events for this specific Incidence.
        Used for the 'Recent Occurrences' tab.
        """

        incidence = self.get_object()
        recent_footprints = incidence.footprint_set.all().order_by('-created_at')[:20]
        serializer = FootprintListSerializer(recent_footprints, many=True)
        return Response(serializer.data)


class FootprintViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Powers the 'Forensics' room.
    """

    queryset = Footprint.objects.all().order_by('-created_at')
    permission_classes = [IsStaff]


    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FootprintDetailSerializer
        return FootprintListSerializer

    @action(detail=True, methods=['get'])
    def breadcrumbs(self, request, pk=None):
        """
        The 'Time Machine': Finds what this user did 5 minutes BEFORE the crash.
        """

        current_footprint = self.get_object()
        user = current_footprint.request_user
        crash_time = current_footprint.created_at

        if not user or user == "anonymous":
            return Response([])

        # Look back 5 minutes max
        start_time = crash_time - timedelta(minutes=5)

        breadcrumbs = Footprint.objects.filter(
            request_user=user,
            created_at__gte=start_time,
            created_at__lt=crash_time
        ).order_by('-created_at')[:10]

        serializer = FootprintListSerializer(breadcrumbs, many=True)
        return Response(serializer.data)


class DashboardStatsView(APIView):
    """
    Powers the 'Dashboard' (Home Page).
    Returns Velocity metrics and Health Cards.
    """
    permission_classes = [IsStaff]

    def get(self, request):
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        recent_qs = Footprint.objects.filter(created_at__gte=last_24h)

        # Velocity Metrics (Counts)
        total_requests = recent_qs.count()
        error_count_500 = recent_qs.filter(status_code__gte=500).count()
        error_count_400 = recent_qs.filter(status_code__gte=400, status_code__lt=500).count()

        # Health Card: Average Response Time
        avg_response = recent_qs.aggregate(avg=Avg('response_time'))['avg'] or 0

        # Impact Scoreboard: Top Offenders (Incidences affecting most users)
        top_incidences = Incidence.objects.filter(status='OPEN').annotate(
            users_affected=Count('footprint__request_user', distinct=True)
        ).order_by('-users_affected')[:5]
        
        top_incidences_data = IncidenceListSerializer(top_incidences, many=True).data

        return Response({
            "velocity": {
                "total_24h": total_requests,
                "errors_500": error_count_500,
                "errors_400": error_count_400,
            },
            "health": {
                "avg_response_time_ms": round(avg_response, 2)
            },
            "top_offenders": top_incidences_data
        })
    

class SettingsViewSet(viewsets.ModelViewSet):
    """
    Powers the 'Settings' page.
    Allows dynamic configuration of the package behavior.
    """

    queryset = InsiderSetting.objects.all().order_by('key')
    serializer_class = InsiderSettingSerializer
    permission_classes = [IsStaff]
    http_method_names = ['get', 'patch', 'head', 'options']

    def list(self, request, *args, **kwargs):
        """
        Auto-Discovery: If settings table is empty, populate it with DEFAULTS.
        This ensures the UI is never empty on first install.
        """
        
        if not self.get_queryset().exists():
            new_settings = []
            
            for key, default_val in DEFAULTS.items():
                # Inference Logic for Field Type
                f_type = 'STRING'
                if isinstance(default_val, bool):
                    f_type = 'BOOLEAN'
                elif isinstance(default_val, int) or default_val is None:
                    f_type = 'INTEGER'
                elif isinstance(default_val, list):
                    f_type = 'LIST'
                
                new_settings.append(InsiderSetting(
                    key=key,
                    value=default_val,
                    field_type=f_type,
                    description=f"Controls {key.replace('_', ' ').lower()}"
                ))
            
            # Bulk Create for efficiency
            InsiderSetting.objects.bulk_create(new_settings)
            
        return super().list(request, *args, **kwargs)

    def perform_update(self, serializer):
        """
        After saving to DB, force the system to reload config 
        so changes apply immediately without restart.
        """
        serializer.save()
        reload_settings()