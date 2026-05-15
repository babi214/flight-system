from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class Airline(models.Model):
    """Airline information"""
    
    class AirlineType(models.TextChoices):
        MAJOR = 'MAJOR', 'Major Carrier'
        LOW_COST = 'LOW_COST', 'Low Cost Carrier'
        REGIONAL = 'REGIONAL', 'Regional'
        CHARTER = 'CHARTER', 'Charter'
    
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=AirlineType.choices, default=AirlineType.MAJOR)
    logo = models.ImageField(upload_to='airline_logos/', null=True, blank=True)
    website = models.URLField(blank=True)
    baggage_allowance = models.IntegerField(default=23, help_text="Kg")
    cabin_baggage = models.IntegerField(default=7, help_text="Kg")
    
    # Loyalty partnerships
    loyalty_program = models.CharField(max_length=100, blank=True)
    alliance = models.CharField(max_length=50, blank=True, choices=[
        ('STAR', 'Star Alliance'),
        ('SKYTEAM', 'SkyTeam'),
        ('ONEWORLD', 'oneworld'),
        ('NONE', 'None'),
    ], default='NONE')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Airport(models.Model):
    """Airport information"""
    
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    timezone = models.CharField(max_length=50)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Airport facilities
    has_lounge = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=True)
    terminal_count = models.IntegerField(default=1)
    
    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['city', 'country']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.city})"
    
    def get_full_address(self):
        return f"{self.name}, {self.city}, {self.country}"


class Aircraft(models.Model):
    """Aircraft information"""
    
    class AircraftType(models.TextChoices):
        NARROW_BODY = 'NARROW', 'Narrow Body'
        WIDE_BODY = 'WIDE', 'Wide Body'
        REGIONAL = 'REGIONAL', 'Regional Jet'
        TURBOPROP = 'TURBO', 'Turboprop'
    
    model = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=AircraftType.choices)
    capacity_economy = models.IntegerField()
    capacity_business = models.IntegerField(default=0)
    capacity_first = models.IntegerField(default=0)
    
    # Aircraft specs
    range_km = models.IntegerField(help_text="Maximum range in kilometers")
    cruise_speed = models.IntegerField(help_text="Cruise speed in km/h")
    fuel_efficiency = models.DecimalField(max_digits=5, decimal_places=2, help_text="L per 100 km")
    
    # Features
    has_wifi = models.BooleanField(default=False)
    has_power_ports = models.BooleanField(default=True)
    has_entertainment = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['manufacturer', 'model']
    
    def __str__(self):
        return f"{self.manufacturer} {self.model}"
    
    @property
    def total_capacity(self):
        return self.capacity_economy + self.capacity_business + self.capacity_first


class Flight(models.Model):
    """Flight schedule and information"""
    
    class FlightStatus(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        DELAYED = 'DELAYED', 'Delayed'
        BOARDING = 'BOARDING', 'Boarding'
        DEPARTED = 'DEPARTED', 'Departing'
        IN_AIR = 'IN_AIR', 'In Air'
        ARRIVED = 'ARRIVED', 'Arrived'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'
    
    class DaysOfWeek(models.TextChoices):
        MON = 'MON', 'Monday'
        TUE = 'TUE', 'Tuesday'
        WED = 'WED', 'Wednesday'
        THU = 'THU', 'Thursday'
        FRI = 'FRI', 'Friday'
        SAT = 'SAT', 'Saturday'
        SUN = 'SUN', 'Sunday'
    
    # Basic info
    flight_number = models.CharField(max_length=10, unique=True)
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, related_name='flights')
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name='flights')
    
    # Route
    origin = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name='departing_flights')
    destination = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name='arriving_flights')
    
    # Times
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    duration_minutes = models.IntegerField(help_text="Flight duration in minutes")
    
    # Recurring flights
    is_recurring = models.BooleanField(default=False)
    recurring_days = models.CharField(max_length=21, blank=True, help_text="Comma-separated days")
    recurring_end_date = models.DateTimeField(null=True, blank=True)
    
    # Capacity and pricing
    total_seats = models.IntegerField()
    available_seats = models.IntegerField()
    base_price_economy = models.DecimalField(max_digits=10, decimal_places=2)
    base_price_business = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    base_price_first = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=FlightStatus.choices, default=FlightStatus.SCHEDULED)
    gate = models.CharField(max_length=10, blank=True)
    terminal = models.CharField(max_length=10, blank=True)
    baggage_claim = models.CharField(max_length=10, blank=True)
    
    # Additional info
    check_in_start = models.DateTimeField(null=True, blank=True)
    check_in_end = models.DateTimeField(null=True, blank=True)
    boarding_start = models.DateTimeField(null=True, blank=True)
    boarding_end = models.DateTimeField(null=True, blank=True)
    
    # Restrictions
    min_advance_booking = models.IntegerField(default=0, help_text="Minimum hours before departure")
    max_advance_booking = models.IntegerField(default=365, help_text="Maximum days before departure")
    refundable = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['departure_time']
        indexes = [
            models.Index(fields=['flight_number']),
            models.Index(fields=['origin', 'destination']),
            models.Index(fields=['departure_time']),
            models.Index(fields=['status']),
            models.Index(fields=['origin', 'departure_time']),
            models.Index(fields=['destination', 'arrival_time']),
        ]
    
    def __str__(self):
        return f"{self.flight_number}: {self.origin.code} → {self.destination.code} ({self.departure_time.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        # Calculate duration if not provided
        if not self.duration_minutes:
            duration = self.arrival_time - self.departure_time
            self.duration_minutes = int(duration.total_seconds() / 60)
        
        # Ensure available_seats doesn't exceed total_seats
        if self.available_seats > self.total_seats:
            self.available_seats = self.total_seats
        
        super().save(*args, **kwargs)
    
    @property
    def is_full(self):
        return self.available_seats == 0
    
    @property
    def occupancy_rate(self):
        return ((self.total_seats - self.available_seats) / self.total_seats) * 100
    
    @property
    def is_delayed(self):
        return self.status == self.FlightStatus.DELAYED
    
    def get_price_for_class(self, cabin_class='ECONOMY'):
        """Get price based on cabin class"""
        if cabin_class == 'FIRST' and self.base_price_first:
            return self.base_price_first
        elif cabin_class == 'BUSINESS' and self.base_price_business:
            return self.base_price_business
        return self.base_price_economy


class FlightSeat(models.Model):
    """Individual seat information for each flight"""
    
    class SeatClass(models.TextChoices):
        ECONOMY = 'ECONOMY', 'Economy'
        PREMIUM_ECONOMY = 'PREMIUM_ECONOMY', 'Premium Economy'
        BUSINESS = 'BUSINESS', 'Business'
        FIRST = 'FIRST', 'First'
    
    class SeatType(models.TextChoices):
        WINDOW = 'WINDOW', 'Window'
        MIDDLE = 'MIDDLE', 'Middle'
        AISLE = 'AISLE', 'Aisle'
        EXTRA_LEG = 'EXTRA_LEG', 'Extra Legroom'
    
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=4)
    seat_class = models.CharField(max_length=20, choices=SeatClass.choices, default=SeatClass.ECONOMY)
    seat_type = models.CharField(max_length=20, choices=SeatType.choices)
    is_available = models.BooleanField(default=True)
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    
    # Features
    has_power = models.BooleanField(default=False)
    has_extra_legroom = models.BooleanField(default=False)
    near_exit = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['flight', 'seat_number']
        indexes = [
            models.Index(fields=['flight', 'is_available']),
            models.Index(fields=['seat_class']),
        ]
    
    def __str__(self):
        return f"{self.flight.flight_number} - Seat {self.seat_number}"
    
    def get_final_price(self, base_price):
        return base_price * self.price_multiplier


class FlightPricing(models.Model):
    """Dynamic pricing for flights"""
    
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='pricing_tiers')
    cabin_class = models.CharField(max_length=20, choices=FlightSeat.SeatClass.choices)
    
    # Pricing buckets
    bucket_name = models.CharField(max_length=50)  # EARLY_BIRD, STANDARD, LAST_MINUTE
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_seats = models.IntegerField()
    
    # Rules
    days_before_departure_min = models.IntegerField()
    days_before_departure_max = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['flight', 'cabin_class', 'bucket_name']
        ordering = ['flight', 'cabin_class', 'price']
    
    def __str__(self):
        return f"{self.flight.flight_number} - {self.cabin_class} - {self.bucket_name}"


class FlightDelay(models.Model):
    """Track flight delays"""
    
    class DelayReason(models.TextChoices):
        WEATHER = 'WEATHER', 'Weather'
        TECHNICAL = 'TECHNICAL', 'Technical Issues'
        AIR_TRAFFIC = 'AIR_TRAFFIC', 'Air Traffic Control'
        CREW = 'CREW', 'Crew Availability'
        SECURITY = 'SECURITY', 'Security'
        OTHER = 'OTHER', 'Other'
    
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='delays')
    scheduled_departure = models.DateTimeField()
    actual_departure = models.DateTimeField()
    delay_minutes = models.IntegerField()
    reason = models.CharField(max_length=20, choices=DelayReason.choices)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['flight', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.flight.flight_number} - {self.delay_minutes} min delay"