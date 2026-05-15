from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FlightViewSet, AirportViewSet, AirlineViewSet, AdminFlightViewSet
)

router = DefaultRouter()
router.register('flights', FlightViewSet, basename='flight')
router.register('airports', AirportViewSet, basename='airport')
router.register('airlines', AirlineViewSet, basename='airline')
router.register('admin/flights', AdminFlightViewSet, basename='admin-flight')

urlpatterns = [
    path('', include(router.urls)),
]