from django.contrib import admin
from django.utils.html import format_html
from .models import Airline, Airport, Aircraft, Flight, FlightSeat, FlightDelay


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'type', 'alliance', 'baggage_allowance']
    list_filter = ['type', 'alliance']
    search_fields = ['code', 'name']
    fieldsets = (
        ('Basic Info', {'fields': ('code', 'name', 'type', 'logo', 'website')}),
        ('Baggage Policy', {'fields': ('baggage_allowance', 'cabin_baggage')}),
        ('Loyalty', {'fields': ('loyalty_program', 'alliance')}),
    )


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'city', 'country', 'has_lounge']
    list_filter = ['country', 'has_lounge', 'has_wifi']
    search_fields = ['code', 'name', 'city', 'country']
    fieldsets = (
        ('Basic Info', {'fields': ('code', 'name', 'city', 'country', 'timezone')}),
        ('Location', {'fields': ('latitude', 'longitude')}),
        ('Facilities', {'fields': ('has_lounge', 'has_wifi', 'terminal_count')}),
        ('Contact', {'fields': ('phone', 'email', 'website')}),
    )


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ['model', 'manufacturer', 'type', 'total_capacity']
    list_filter = ['type', 'has_wifi']
    search_fields = ['model', 'manufacturer']


class FlightSeatInline(admin.TabularInline):
    model = FlightSeat
    extra = 0
    fields = ['seat_number', 'seat_class', 'seat_type', 'is_available']


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = [
        'flight_number', 'airline', 'origin', 'destination',
        'departure_time', 'available_seats', 'status', 'colored_status'
    ]
    list_filter = ['status', 'airline', 'origin', 'destination', 'departure_time']
    search_fields = ['flight_number', 'origin__code', 'destination__code']
    filter_horizontal = []
    raw_id_fields = ['origin', 'destination', 'airline', 'aircraft']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Flight Info', {
            'fields': ('flight_number', 'airline', 'aircraft', 'status')
        }),
        ('Route', {
            'fields': ('origin', 'destination', 'departure_time', 'arrival_time', 'duration_minutes')
        }),
        ('Capacity & Pricing', {
            'fields': ('total_seats', 'available_seats', 'base_price_economy', 
                      'base_price_business', 'base_price_first')
        }),
        ('Operations', {
            'fields': ('gate', 'terminal', 'baggage_claim', 'check_in_start', 
                      'check_in_end', 'boarding_start', 'boarding_end')
        }),
        ('Recurring', {
            'fields': ('is_recurring', 'recurring_days', 'recurring_end_date'),
            'classes': ('collapse',)
        }),
        ('Restrictions', {
            'fields': ('min_advance_booking', 'max_advance_booking', 'refundable'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [FlightSeatInline]
    
    def colored_status(self, obj):
        colors = {
            'SCHEDULED': 'green',
            'DELAYED': 'orange',
            'BOARDING': 'blue',
            'DEPARTED': 'purple',
            'ARRIVED': 'gray',
            'CANCELLED': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    colored_status.short_description = 'Status'


@admin.register(FlightDelay)
class FlightDelayAdmin(admin.ModelAdmin):
    list_display = ['flight', 'delay_minutes', 'reason', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['flight__flight_number']
    readonly_fields = ['created_at']


@admin.register(FlightSeat)
class FlightSeatAdmin(admin.ModelAdmin):
    list_display = ['flight', 'seat_number', 'seat_class', 'is_available', 'price_multiplier']
    list_filter = ['seat_class', 'seat_type', 'is_available']
    search_fields = ['flight__flight_number', 'seat_number']