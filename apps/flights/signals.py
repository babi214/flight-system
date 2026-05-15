from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Flight, FlightSeat


@receiver(pre_save, sender=Flight)
def update_flight_duration(sender, instance, **kwargs):
    """Auto-calculate flight duration if not provided"""
    if not instance.duration_minutes and instance.arrival_time and instance.departure_time:
        duration = instance.arrival_time - instance.departure_time
        instance.duration_minutes = int(duration.total_seconds() / 60)


@receiver(post_save, sender=Flight)
def create_flight_seats(sender, instance, created, **kwargs):
    """Automatically create seats when a new flight is created"""
    if created:
        # Create economy seats
        for row in range(1, (instance.total_seats // 6) + 1):
            for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
                seat_number = f"{row}{letter}"
                
                # Determine seat type
                if letter in ['A', 'F']:
                    seat_type = 'WINDOW'
                elif letter in ['C', 'D']:
                    seat_type = 'AISLE'
                else:
                    seat_type = 'MIDDLE'
                
                # Extra legroom for exit rows
                has_extra_legroom = row in [1, instance.total_seats // 6]
                near_exit = row in [1, instance.total_seats // 6]
                
                FlightSeat.objects.create(
                    flight=instance,
                    seat_number=seat_number,
                    seat_class='ECONOMY',
                    seat_type=seat_type,
                    is_available=True,
                    price_multiplier=1.5 if has_extra_legroom else 1.0,
                    has_extra_legroom=has_extra_legroom,
                    near_exit=near_exit
                )