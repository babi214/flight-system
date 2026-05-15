from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Q, Min, Max, Avg
from django.core.cache import cache
from .models import Flight, Airport, Airline
from .route_optimizer import FlightRouteOptimizer, FlightConnection


class FlightSearchService:
    """Service for flight search and availability"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        passengers: int = 1,
        cabin_class: str = 'ECONOMY',
        direct_only: bool = False,
        sort_by: str = 'price',
        sort_order: str = 'asc',
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        airline: Optional[str] = None
    ) -> List[Flight]:
        """Search for available flights"""
        
        # Build cache key
        cache_key = f"flight_search_{origin}_{destination}_{departure_date.date()}_{passengers}_{cabin_class}_{direct_only}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Base query
        start_datetime = datetime.combine(departure_date.date(), datetime.min.time())
        end_datetime = datetime.combine(departure_date.date(), datetime.max.time())
        
        queryset = Flight.objects.filter(
            origin__code=origin,
            destination__code=destination,
            departure_time__range=(start_datetime, end_datetime),
            available_seats__gte=passengers,
            status='SCHEDULED'
        ).select_related('origin', 'destination', 'airline', 'aircraft')
        
        # Apply filters
        if min_price:
            queryset = queryset.filter(base_price_economy__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price_economy__lte=max_price)
        if airline:
            queryset = queryset.filter(airline__code=airline)
        
        # Apply sorting
        sort_field = {
            'price': 'base_price_economy',
            'duration': 'duration_minutes',
            'departure_time': 'departure_time',
            'arrival_time': 'arrival_time'
        }.get(sort_by, 'base_price_economy')
        
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'
        
        queryset = queryset.order_by(sort_field)
        
        # Cache results
        results = list(queryset[:100])  # Limit to 100 results
        cache.set(cache_key, results, self.cache_timeout)
        
        return results
    
    def get_flight_availability(self, flight_id: int) -> Dict:
        """Get detailed availability for a flight"""
        
        cache_key = f"flight_availability_{flight_id}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        try:
            flight = Flight.objects.select_related('origin', 'destination').get(id=flight_id)
            
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
            
            cache.set(cache_key, availability, 60)  # Cache for 1 minute
            return availability
            
        except Flight.DoesNotExist:
            return None
    
    def get_popular_routes(self, limit: int = 10) -> List[Dict]:
        """Get most popular flight routes"""
        
        cache_key = "popular_routes"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        popular = Flight.objects.values(
            'origin__code', 'origin__city',
            'destination__code', 'destination__city'
        ).annotate(
            flight_count=models.Count('id'),
            avg_price=models.Avg('base_price_economy'),
            min_price=models.Min('base_price_economy'),
            avg_duration=models.Avg('duration_minutes')
        ).order_by('-flight_count')[:limit]
        
        results = []
        for route in popular:
            results.append({
                'origin': {
                    'code': route['origin__code'],
                    'city': route['origin__city']
                },
                'destination': {
                    'code': route['destination__code'],
                    'city': route['destination__city']
                },
                'flight_count': route['flight_count'],
                'avg_price': float(route['avg_price']),
                'min_price': float(route['min_price']),
                'avg_duration_minutes': route['avg_duration']
            })
        
        cache.set(cache_key, results, 3600)  # Cache for 1 hour
        return results


class FlightRouteService:
    """Service for complex route optimization"""
    
    def __init__(self):
        self.optimizer = FlightRouteOptimizer(max_layovers=2)
    
    def find_connections(
        self,
        origin: str,
        destination: str,
        date: datetime,
        optimization: str = 'cheapest'
    ) -> Optional[Dict]:
        """Find flight connections with layovers"""
        
        # Get all flights for the day
        start_datetime = datetime.combine(date.date(), datetime.min.time())
        end_datetime = datetime.combine(date.date(), datetime.max.time())
        
        flights = Flight.objects.filter(
            Q(origin__code=origin) | Q(destination__code=destination),
            departure_time__range=(start_datetime, end_datetime),
            available_seats__gt=0,
            status='SCHEDULED'
        ).select_related('origin', 'destination', 'airline')
        
        # Convert to FlightConnection objects
        connections = []
        for flight in flights:
            connections.append(FlightConnection(
                flight_id=flight.id,
                flight_number=flight.flight_number,
                origin=flight.origin.code,
                destination=flight.destination.code,
                departure_time=flight.departure_time,
                arrival_time=flight.arrival_time,
                price=flight.base_price_economy,
                airline=flight.airline.code,
                available_seats=flight.available_seats
            ))
        
        # Find route based on optimization type
        if optimization == 'cheapest':
            route = self.optimizer.find_cheapest_route(
                connections, origin, destination, start_datetime
            )
        elif optimization == 'fastest':
            route = self.optimizer.find_fastest_route(
                connections, origin, destination, start_datetime
            )
        else:  # balanced
            route = self.optimizer.find_balanced_route(
                connections, origin, destination, start_datetime,
                price_weight=0.5, time_weight=0.5
            )
        
        if route:
            return {
                'total_price': float(route.total_price),
                'total_flight_duration': route.total_flight_duration,
                'total_journey_duration': route.total_journey_duration,
                'layovers': route.layovers,
                'segments': route.segments,
                'route_details': route.get_detailed_route()
            }
        
        return None
    
    def find_multi_city_route(
        self,
        cities: List[str],
        start_date: datetime
    ) -> List[Dict]:
        """Find route connecting multiple cities"""
        
        routes = []
        current_date = start_date
        current_city = cities[0]
        
        for i in range(1, len(cities)):
            next_city = cities[i]
            
            route = self.find_connections(
                current_city, next_city, current_date, 'cheapest'
            )
            
            if route:
                # Update arrival date for next leg
                last_flight = route['route_details'][-1]
                current_date = datetime.fromisoformat(last_flight['arrival'])
                
                routes.append({
                    'from': current_city,
                    'to': next_city,
                    'route': route
                })
                
                current_city = next_city
            else:
                routes.append({
                    'from': current_city,
                    'to': next_city,
                    'route': None,
                    'error': 'No route found'
                })
                break
        
        return routes


class PriceAlertService:
    """Service for price monitoring and alerts"""
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour
    
    def get_price_trends(self, origin: str, destination: str, days: int = 30) -> Dict:
        """Get price trends for a route"""
        
        cache_key = f"price_trends_{origin}_{destination}_{days}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        prices = Flight.objects.filter(
            origin__code=origin,
            destination__code=destination,
            departure_time__range=(start_date, end_date)
        ).values('departure_time__date').annotate(
            min_price=Min('base_price_economy'),
            max_price=Max('base_price_economy'),
            avg_price=Avg('base_price_economy')
        ).order_by('departure_time__date')
        
        result = {
            'route': f"{origin} → {destination}",
            'period_days': days,
            'price_history': list(prices),
            'best_price': min(p['min_price'] for p in prices) if prices else None,
            'worst_price': max(p['max_price'] for p in prices) if prices else None
        }
        
        cache.set(cache_key, result, self.cache_timeout)
        return result
    
    def check_for_price_drop(self, user_id: int, route_id: int) -> bool:
        """Check if price dropped for a saved route"""
        # Implementation for price drop alerts
        pass