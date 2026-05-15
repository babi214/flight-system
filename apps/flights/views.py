from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.cache import cache
from datetime import datetime
from .models import Flight, Airport, Airline, Aircraft
from .serializers import (
    FlightListSerializer, FlightDetailSerializer, FlightSearchSerializer,
    FlightRouteSerializer, AirportSerializer, AirlineSerializer,
    AircraftSerializer, FlightCreateSerializer, FlightDelaySerializer
)
from .filters import FlightFilter, AirportFilter, AirlineFilter
from .services import FlightSearchService, FlightRouteService


class FlightViewSet(viewsets.ReadOnlyModelViewSet):
    """Flight viewset for search and retrieval"""
    
    queryset = Flight.objects.select_related(
        'origin', 'destination', 'airline', 'aircraft'
    ).all()
    serializer_class = FlightListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FlightFilter
    search_fields = ['flight_number', 'origin__code', 'destination__code', 'airline__name']
    ordering_fields = ['departure_time', 'base_price_economy', 'duration_minutes']
    ordering = ['departure_time']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FlightDetailSerializer
        return FlightListSerializer
    
    @action(detail=False, methods=['get'], url_path='search', permission_classes=[AllowAny])
    def search_flights(self, request):
        """Advanced flight search with filters"""
        serializer = FlightSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        search_service = FlightSearchService()
        flights = search_service.search_flights(
            origin=data['origin'],
            destination=data['destination'],
            departure_date=data['departure_date'],
            passengers=data['passengers'],
            cabin_class=data['cabin_class'],
            direct_only=data['direct_only'],
            sort_by=data['sort_by'],
            sort_order=data['sort_order'],
            min_price=data.get('min_price'),
            max_price=data.get('max_price'),
            airline=data.get('airline')
        )
        
        # Handle round trip if return_date provided
        if data.get('return_date'):
            return_flights = search_service.search_flights(
                origin=data['destination'],
                destination=data['origin'],
                departure_date=data['return_date'],
                passengers=data['passengers'],
                cabin_class=data['cabin_class'],
                direct_only=data['direct_only'],
                sort_by=data['sort_by'],
                sort_order=data['sort_order']
            )
            
            return Response({
                'outbound': FlightListSerializer(flights, many=True).data,
                'return': FlightListSerializer(return_flights, many=True).data,
                'search_params': data
            })
        
        serializer = FlightListSerializer(flights, many=True)
        return Response({
            'results': serializer.data,
            'count': len(flights),
            'search_params': data
        })
    
    @action(detail=False, methods=['post'], url_path='route/optimize')
    def optimize_route(self, request):
        """Find optimized route with layovers"""
        serializer = FlightRouteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        route_service = FlightRouteService()
        route = route_service.find_connections(
            origin=data['origin'],
            destination=data['destination'],
            date=data['date'],
            optimization=request.query_params.get('optimization', 'cheapest')
        )
        
        if route:
            return Response(route)
        
        return Response(
            {"error": "No route found with the given criteria"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=True, methods=['get'], url_path='availability')
    def check_availability(self, request, pk=None):
        """Check seat availability for a flight"""
        flight = self.get_object()
        
        availability = {
            'flight_id': flight.id,
            'flight_number': flight.flight_number,
            'total_seats': flight.total_seats,
            'available_seats': flight.available_seats,
            'occupancy_rate': flight.occupancy_rate,
            'is_full': flight.is_full,
            'prices': {
                'economy': float(flight.base_price_economy),
                'business': float(flight.base_price_business) if flight.base_price_business else None,
                'first': float(flight.base_price_first) if flight.base_price_first else None
            }
        }
        
        return Response(availability)
    
    @action(detail=False, methods=['get'], url_path='popular-routes')
    def popular_routes(self, request):
        """Get most popular flight routes"""
        search_service = FlightSearchService()
        routes = search_service.get_popular_routes(limit=10)
        return Response(routes)
    
    @action(detail=False, methods=['get'], url_path='price-trends')
    def price_trends(self, request):
        """Get price trends for a route"""
        origin = request.query_params.get('origin')
        destination = request.query_params.get('destination')
        days = int(request.query_params.get('days', 30))
        
        if not origin or not destination:
            return Response(
                {"error": "origin and destination parameters required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        search_service = FlightSearchService()
        trends = search_service.get_price_trends(origin, destination, days)
        return Response(trends)
    
    @action(detail=False, methods=['get'], url_path='nearby-airports')
    def nearby_airports(self, request):
        """Find nearby airports (simplified)"""
        airport_code = request.query_params.get('code')
        radius_km = int(request.query_params.get('radius', 100))
        
        if not airport_code:
            return Response(
                {"error": "airport_code parameter required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            airport = Airport.objects.get(code=airport_code)
            
            # Simplified: return airports in same city or country
            nearby = Airport.objects.filter(
                Q(city=airport.city) | Q(country=airport.country)
            ).exclude(code=airport_code)[:10]
            
            serializer = AirportSerializer(nearby, many=True)
            return Response({
                'origin_airport': AirportSerializer(airport).data,
                'nearby_airports': serializer.data
            })
        except Airport.DoesNotExist:
            return Response(
                {"error": "Airport not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class AirportViewSet(viewsets.ReadOnlyModelViewSet):
    """Airport management"""
    
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = AirportFilter
    search_fields = ['code', 'name', 'city', 'country']
    
    @action(detail=False, methods=['get'], url_path='popular')
    def popular_airports(self, request):
        """Get most popular airports (with most flights)"""
        popular = Airport.objects.annotate(
            flight_count=models.Count('departing_flights')
        ).order_by('-flight_count')[:20]
        
        serializer = AirportSerializer(popular, many=True)
        return Response(serializer.data)


class AirlineViewSet(viewsets.ReadOnlyModelViewSet):
    """Airline management"""
    
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = AirlineFilter
    search_fields = ['code', 'name']


class AdminFlightViewSet(viewsets.ModelViewSet):
    """Admin only: Create, update, delete flights"""
    
    queryset = Flight.objects.all()
    serializer_class = FlightCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.user_type == 'ADMIN':
            return Flight.objects.all()
        return Flight.objects.none()
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_flight(self, request, pk=None):
        """Cancel a flight"""
        flight = self.get_object()
        flight.status = 'CANCELLED'
        flight.save()
        
        # TODO: Notify all booked passengers
        return Response({"message": "Flight cancelled successfully"})
    
    @action(detail=True, methods=['post'], url_path='delay')
    def report_delay(self, request, pk=None):
        """Report flight delay"""
        flight = self.get_object()
        serializer = FlightDelaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        delay = serializer.save(flight=flight)
        flight.status = 'DELAYED'
        flight.save()
        
        return Response(FlightDelaySerializer(delay).data, status=status.HTTP_201_CREATED)