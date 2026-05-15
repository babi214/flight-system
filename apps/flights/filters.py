from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Flight, Airport, Airline


class FlightFilter(filters.FilterSet):
    """Advanced filtering for flights"""
    
    # Basic filters
    origin = filters.CharFilter(field_name='origin__code', lookup_expr='iexact')
    destination = filters.CharFilter(field_name='destination__code', lookup_expr='iexact')
    origin_city = filters.CharFilter(field_name='origin__city', lookup_expr='icontains')
    destination_city = filters.CharFilter(field_name='destination__city', lookup_expr='icontains')
    
    # Date filters
    departure_date = filters.DateFilter(field_name='departure_time', lookup_expr='date')
    departure_date_from = filters.DateFilter(field_name='departure_time', lookup_expr='date__gte')
    departure_date_to = filters.DateFilter(field_name='departure_time', lookup_expr='date__lte')
    departure_time_from = filters.TimeFilter(field_name='departure_time', lookup_expr='time__gte')
    departure_time_to = filters.TimeFilter(field_name='departure_time', lookup_expr='time__lte')
    
    arrival_date = filters.DateFilter(field_name='arrival_time', lookup_expr='date')
    
    # Time range filters
    departure_after = filters.DateTimeFilter(field_name='departure_time', lookup_expr='gte')
    departure_before = filters.DateTimeFilter(field_name='departure_time', lookup_expr='lte')
    
    # Price filters
    min_price = filters.NumberFilter(field_name='base_price_economy', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='base_price_economy', lookup_expr='lte')
    
    # Airline filters
    airline = filters.CharFilter(field_name='airline__code', lookup_expr='iexact')
    airline_name = filters.CharFilter(field_name='airline__name', lookup_expr='icontains')
    
    # Aircraft filters
    aircraft_type = filters.CharFilter(field_name='aircraft__type', lookup_expr='iexact')
    
    # Duration filters
    max_duration = filters.NumberFilter(field_name='duration_minutes', lookup_expr='lte')
    min_duration = filters.NumberFilter(field_name='duration_minutes', lookup_expr='gte')
    
    # Status filters
    status = filters.CharFilter(field_name='status', lookup_expr='iexact')
    
    # Availability
    has_seats = filters.BooleanFilter(method='filter_has_seats')
    
    # Search across multiple fields
    search = filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Flight
        fields = [
            'origin', 'destination', 'origin_city', 'destination_city',
            'departure_date', 'departure_date_from', 'departure_date_to',
            'airline', 'status', 'min_price', 'max_price'
        ]
    
    def filter_has_seats(self, queryset, name, value):
        if value:
            return queryset.filter(available_seats__gt=0)
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across flight number, airport names, cities"""
        return queryset.filter(
            Q(flight_number__icontains=value) |
            Q(origin__code__icontains=value) |
            Q(origin__name__icontains=value) |
            Q(origin__city__icontains=value) |
            Q(destination__code__icontains=value) |
            Q(destination__name__icontains=value) |
            Q(destination__city__icontains=value) |
            Q(airline__name__icontains=value) |
            Q(airline__code__icontains=value)
        )


class AirportFilter(filters.FilterSet):
    """Filter airports"""
    
    search = filters.CharFilter(method='filter_search')
    country = filters.CharFilter(field_name='country', lookup_expr='iexact')
    has_lounge = filters.BooleanFilter(field_name='has_lounge')
    
    class Meta:
        model = Airport
        fields = ['country', 'city', 'has_lounge']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(code__icontains=value) |
            Q(name__icontains=value) |
            Q(city__icontains=value) |
            Q(country__icontains=value)
        )


class AirlineFilter(filters.FilterSet):
    """Filter airlines"""
    
    search = filters.CharFilter(method='filter_search')
    alliance = filters.CharFilter(field_name='alliance', lookup_expr='iexact')
    
    class Meta:
        model = Airline
        fields = ['type', 'alliance']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(code__icontains=value) |
            Q(name__icontains=value)
        )