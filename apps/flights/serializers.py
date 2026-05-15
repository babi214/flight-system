from rest_framework import serializers
from .models import (
    Airline, Airport, Aircraft, Flight, 
    FlightSeat, FlightPricing, FlightDelay
)


class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = [
            'id', 'code', 'name', 'type', 'logo', 'website',
            'baggage_allowance', 'cabin_baggage', 'loyalty_program',
            'alliance', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AirportSerializer(serializers.ModelSerializer):
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Airport
        fields = [
            'id', 'code', 'name', 'city', 'country', 'timezone',
            'latitude', 'longitude', 'has_lounge', 'has_wifi',
            'terminal_count', 'phone', 'email', 'website',
            'full_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_full_address(self, obj):
        return obj.get_full_address()


class AircraftSerializer(serializers.ModelSerializer):
    total_capacity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Aircraft
        fields = [
            'id', 'model', 'manufacturer', 'type', 'capacity_economy',
            'capacity_business', 'capacity_first', 'total_capacity',
            'range_km', 'cruise_speed', 'fuel_efficiency',
            'has_wifi', 'has_power_ports', 'has_entertainment',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FlightSeatSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()
    
    class Meta:
        model = FlightSeat
        fields = [
            'id', 'seat_number', 'seat_class', 'seat_type',
            'is_available', 'price_multiplier', 'final_price',
            'has_power', 'has_extra_legroom', 'near_exit'
        ]
        read_only_fields = ['id']
    
    def get_final_price(self, obj):
        base_price = obj.flight.get_price_for_class(obj.seat_class)
        return float(base_price * obj.price_multiplier)


class FlightListSerializer(serializers.ModelSerializer):
    """Simplified serializer for flight listings"""
    origin_code = serializers.CharField(source='origin.code')
    origin_city = serializers.CharField(source='origin.city')
    destination_code = serializers.CharField(source='destination.code')
    destination_city = serializers.CharField(source='destination.city')
    airline_name = serializers.CharField(source='airline.name')
    airline_code = serializers.CharField(source='airline.code')
    
    class Meta:
        model = Flight
        fields = [
            'id', 'flight_number', 'airline_name', 'airline_code',
            'origin_code', 'origin_city', 'destination_code', 'destination_city',
            'departure_time', 'arrival_time', 'duration_minutes',
            'available_seats', 'base_price_economy', 'status', 'gate', 'terminal'
        ]


class FlightDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single flight"""
    origin = AirportSerializer(read_only=True)
    destination = AirportSerializer(read_only=True)
    airline = AirlineSerializer(read_only=True)
    aircraft = AircraftSerializer(read_only=True)
    seats = FlightSeatSerializer(many=True, read_only=True)
    
    # Additional computed fields
    is_full = serializers.BooleanField(read_only=True)
    occupancy_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Flight
        fields = [
            'id', 'flight_number', 'airline', 'aircraft',
            'origin', 'destination', 'departure_time', 'arrival_time',
            'duration_minutes', 'total_seats', 'available_seats',
            'base_price_economy', 'base_price_business', 'base_price_first',
            'status', 'gate', 'terminal', 'baggage_claim',
            'check_in_start', 'check_in_end', 'boarding_start', 'boarding_end',
            'is_recurring', 'recurring_days', 'min_advance_booking',
            'max_advance_booking', 'refundable', 'is_full', 'occupancy_rate',
            'seats', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FlightSearchSerializer(serializers.Serializer):
    """Serializer for flight search parameters"""
    origin = serializers.CharField(max_length=3, required=True)
    destination = serializers.CharField(max_length=3, required=True)
    departure_date = serializers.DateField(required=True)
    return_date = serializers.DateField(required=False, allow_null=True)
    passengers = serializers.IntegerField(min_value=1, max_value=9, default=1)
    cabin_class = serializers.ChoiceField(
        choices=['ECONOMY', 'BUSINESS', 'FIRST'],
        default='ECONOMY'
    )
    direct_only = serializers.BooleanField(default=False)
    max_layovers = serializers.IntegerField(min_value=0, max_value=3, default=2)
    sort_by = serializers.ChoiceField(
        choices=['price', 'duration', 'departure_time', 'arrival_time'],
        default='price'
    )
    sort_order = serializers.ChoiceField(
        choices=['asc', 'desc'],
        default='asc'
    )
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    airline = serializers.CharField(max_length=3, required=False)
    departure_time_from = serializers.TimeField(required=False)
    departure_time_to = serializers.TimeField(required=False)


class FlightRouteSerializer(serializers.Serializer):
    """Serializer for multi-city route finding"""
    origin = serializers.CharField(max_length=3, required=True)
    destination = serializers.CharField(max_length=3, required=True)
    date = serializers.DateField(required=True)
    departure_after = serializers.DateTimeField(required=False)
    max_layovers = serializers.IntegerField(min_value=0, max_value=3, default=2)
    max_wait_hours = serializers.IntegerField(min_value=1, max_value=24, default=12)


class FlightCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating flights (Admin only)"""
    
    class Meta:
        model = Flight
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate flight data"""
        if data['departure_time'] >= data['arrival_time']:
            raise serializers.ValidationError(
                "Departure time must be before arrival time"
            )
        
        if data['available_seats'] > data['total_seats']:
            raise serializers.ValidationError(
                "Available seats cannot exceed total seats"
            )
        
        return data


class FlightDelaySerializer(serializers.ModelSerializer):
    flight_number = serializers.CharField(source='flight.flight_number', read_only=True)
    
    class Meta:
        model = FlightDelay
        fields = [
            'id', 'flight', 'flight_number', 'scheduled_departure',
            'actual_departure', 'delay_minutes', 'reason', 'description',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FlightPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightPricing
        fields = [
            'id', 'flight', 'cabin_class', 'bucket_name', 'price',
            'available_seats', 'days_before_departure_min',
            'days_before_departure_max', 'created_at', 'updated_at'
        ]