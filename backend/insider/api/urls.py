from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IncidenceViewSet, FootprintViewSet, 
    DashboardStatsView, SettingsViewSet,
    IntegrationViewSet
)

router = DefaultRouter()
router.register(r'incidences', IncidenceViewSet, basename='incidence')
router.register(r'footprints', FootprintViewSet, basename='footprint')
router.register(r'settings', SettingsViewSet, basename='settings')
router.register(r'integrations', IntegrationViewSet, basename='integration')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]