from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncidenceViewSet, FootprintViewSet, DashboardStatsView

router = DefaultRouter()
router.register(r'incidences', IncidenceViewSet, basename='incidence')
router.register(r'footprints', FootprintViewSet, basename='footprint')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/dashboard/', DashboardStatsView.as_view(), name='dashboard-stats'),
]