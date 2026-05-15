from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
import heapq


@dataclass
class FlightConnection:
    """Represents a flight connection for routing"""
    flight_id: int
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    price: Decimal
    airline: str
    available_seats: int


@dataclass
class Route:
    """Represents a complete route with connections"""
    flights: List[FlightConnection]
    total_price: Decimal
    total_flight_duration: int  # minutes
    total_journey_duration: int  # minutes including layovers
    layovers: List[int]  # layover durations in minutes
    
    @property
    def layover_count(self) -> int:
        return len(self.layovers)
    
    @property
    def segments(self) -> int:
        return len(self.flights)
    
    def get_detailed_route(self) -> List[Dict]:
        """Get detailed route information"""
        route_details = []
        for i, flight in enumerate(self.flights):
            detail = {
                'segment': i + 1,
                'flight_number': flight.flight_number,
                'airline': flight.airline,
                'origin': flight.origin,
                'destination': flight.destination,
                'departure': flight.departure_time.isoformat(),
                'arrival': flight.arrival_time.isoformat(),
                'duration_minutes': int((flight.arrival_time - flight.departure_time).total_seconds() / 60),
                'price': float(flight.price)
            }
            
            if i < len(self.layovers):
                detail['layover_minutes'] = self.layovers[i]
            
            route_details.append(detail)
        
        return route_details


class FlightRouteOptimizer:
    """Advanced flight route optimization using Dijkstra's algorithm"""
    
    def __init__(self, max_layovers: int = 2, max_layover_hours: int = 12):
        self.max_layovers = max_layovers
        self.max_layover_hours = max_layover_hours
    
    def find_cheapest_route(
        self,
        flights: List[FlightConnection],
        origin: str,
        destination: str,
        departure_after: datetime
    ) -> Optional[Route]:
        """Find cheapest route using Dijkstra's algorithm"""
        
        # Build graph
        graph = self._build_graph(flights)
        
        # Priority queue: (total_price, layover_count, current_airport, arrival_time, path)
        pq = [(Decimal('0'), 0, origin, departure_after, [])]
        
        # Visited states: (airport, layover_count) -> (best_price, best_arrival_time)
        visited = {}
        
        while pq:
            total_price, layovers, airport, arrival_time, path = heapq.heappop(pq)
            
            # Reached destination
            if airport == destination:
                return self._build_route(path)
            
            # Skip if max layovers exceeded
            if layovers >= self.max_layovers:
                continue
            
            # Check if we've found a better path to this state
            state_key = (airport, layovers)
            if state_key in visited:
                prev_price, prev_time = visited[state_key]
                if prev_price <= total_price and prev_time <= arrival_time:
                    continue
            visited[state_key] = (total_price, arrival_time)
            
            # Explore outgoing flights
            for flight in graph.get(airport, []):
                # Flight must depart after arrival at current airport
                if flight.departure_time < arrival_time:
                    continue
                
                # Check layover duration
                if path:
                    last_flight = path[-1]
                    layover = (flight.departure_time - last_flight.arrival_time).total_seconds() / 60
                    if layover > self.max_layover_hours * 60:
                        continue
                    if layover < 30:  # Minimum 30 minutes layover
                        continue
                
                # Check seat availability
                if flight.available_seats <= 0:
                    continue
                
                new_price = total_price + flight.price
                new_path = path + [flight]
                
                heapq.heappush(pq, (
                    new_price,
                    layovers + 1,
                    flight.destination,
                    flight.arrival_time,
                    new_path
                ))
        
        return None
    
    def find_fastest_route(
        self,
        flights: List[FlightConnection],
        origin: str,
        destination: str,
        departure_after: datetime
    ) -> Optional[Route]:
        """Find fastest route (minimizing total journey time)"""
        
        graph = self._build_graph(flights)
        
        # Priority queue: (arrival_time, layover_count, current_airport, departure_time, path)
        pq = [(departure_after, 0, origin, departure_after, [])]
        visited = {}
        
        while pq:
            arrival_time, layovers, airport, departure, path = heapq.heappop(pq)
            
            if airport == destination:
                return self._build_route(path)
            
            if layovers >= self.max_layovers:
                continue
            
            state_key = (airport, layovers)
            if state_key in visited and visited[state_key] <= arrival_time:
                continue
            visited[state_key] = arrival_time
            
            for flight in graph.get(airport, []):
                if flight.departure_time < departure:
                    continue
                
                if path:
                    last_flight = path[-1]
                    layover = (flight.departure_time - last_flight.arrival_time).total_seconds() / 60
                    if layover > self.max_layover_hours * 60 or layover < 30:
                        continue
                
                new_arrival = flight.arrival_time
                heapq.heappush(pq, (
                    new_arrival,
                    layovers + 1,
                    flight.destination,
                    flight.arrival_time,
                    path + [flight]
                ))
        
        return None
    
    def find_balanced_route(
        self,
        flights: List[FlightConnection],
        origin: str,
        destination: str,
        departure_after: datetime,
        price_weight: float = 0.5,
        time_weight: float = 0.5
    ) -> Optional[Route]:
        """Find balanced route considering both price and time"""
        
        # Find cheapest and fastest for normalization
        cheapest = self.find_cheapest_route(flights, origin, destination, departure_after)
        fastest = self.find_fastest_route(flights, origin, destination, departure_after)
        
        if not cheapest or not fastest:
            return cheapest or fastest
        
        min_price = cheapest.total_price
        min_time = fastest.total_journey_duration
        
        graph = self._build_graph(flights)
        
        # Priority queue with weighted score
        pq = [(0, 0, origin, departure_after, [])]  # (score, layovers, airport, arrival, path)
        visited = {}
        
        while pq:
            score, layovers, airport, arrival_time, path = heapq.heappop(pq)
            
            if airport == destination:
                return self._build_route(path)
            
            if layovers >= self.max_layovers:
                continue
            
            state_key = (airport, layovers)
            if state_key in visited and visited[state_key] <= score:
                continue
            visited[state_key] = score
            
            for flight in graph.get(airport, []):
                if flight.departure_time < arrival_time:
                    continue
                
                if path:
                    last_flight = path[-1]
                    layover = (flight.departure_time - last_flight.arrival_time).total_seconds() / 60
                    if layover > self.max_layover_hours * 60 or layover < 30:
                        continue
                
                new_path = path + [flight]
                temp_route = self._build_route(new_path)
                
                if temp_route:
                    # Normalize and combine scores
                    price_score = float(temp_route.total_price / min_price) if min_price > 0 else 0
                    time_score = temp_route.total_journey_duration / min_time if min_time > 0 else 0
                    
                    combined_score = (price_weight * price_score) + (time_weight * time_score)
                    
                    heapq.heappush(pq, (
                        combined_score,
                        layovers + 1,
                        flight.destination,
                        flight.arrival_time,
                        new_path
                    ))
        
        return None
    
    def _build_graph(self, flights: List[FlightConnection]) -> Dict[str, List[FlightConnection]]:
        """Build adjacency graph from flights"""
        graph = {}
        for flight in flights:
            if flight.origin not in graph:
                graph[flight.origin] = []
            graph[flight.origin].append(flight)
        
        # Sort flights by departure time for each origin
        for origin in graph:
            graph[origin].sort(key=lambda f: f.departure_time)
        
        return graph
    
    def _build_route(self, path: List[FlightConnection]) -> Route:
        """Build Route object from flight path"""
        if not path:
            return None
        
        # Calculate layovers
        layovers = []
        for i in range(len(path) - 1):
            layover = (path[i+1].departure_time - path[i].arrival_time).total_seconds() / 60
            layovers.append(int(layover))
        
        # Calculate total flight duration
        total_flight_duration = sum(
            int((f.arrival_time - f.departure_time).total_seconds() / 60)
            for f in path
        )
        
        # Calculate total journey duration
        total_journey_duration = total_flight_duration + sum(layovers)
        
        # Calculate total price
        total_price = sum(f.price for f in path)
        
        return Route(
            flights=path,
            total_price=total_price,
            total_flight_duration=total_flight_duration,
            total_journey_duration=total_journey_duration,
            layovers=layovers
        )