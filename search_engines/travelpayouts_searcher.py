"""
TravelPayouts API search engine for finding cheap flights
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)


class TravelPayoutsSearcher:
    """Search flights using TravelPayouts API"""
    
    BASE_URL = "https://api.travelpayouts.com"
    
    def __init__(self, token: str):
        """Initialize TravelPayouts searcher
        
        Args:
            token: TravelPayouts API token
        """
        self.token = token
        self.session = requests.Session()
        
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str = None,
        adults: int = 1,
        max_stops: int = 2
    ) -> List[Dict[str, Any]]:
        """Search for flights
        
        Args:
            origin: IATA code of departure airport
            destination: IATA code of destination airport
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD), optional for one-way
            adults: Number of adults
            max_stops: Maximum number of stops
            
        Returns:
            List of flight deals
        """
        try:
            endpoint = f"{self.BASE_URL}/v2/search"
            
            params = {
                "token": self.token,
                "origin": origin,
                "destination": destination,
                "departure_at": departure_date,
                "return_at": return_date,
                "adults": adults,
                "limit": 1000
            }
            
            logger.info(f"Searching TravelPayouts: {origin} → {destination} ({departure_date})")
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            flights = self._parse_response(data, max_stops)
            
            logger.info(f"Found {len(flights)} flights from TravelPayouts")
            return flights
            
        except requests.exceptions.RequestException as e:
            logger.error(f"TravelPayouts search error: {str(e)}")
            return []
    
    def get_cheap_routes(self, origin: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get cheapest destinations from origin
        
        Args:
            origin: IATA code of departure airport
            limit: Maximum routes to return
            
        Returns:
            List of cheap destinations
        """
        try:
            endpoint = f"{self.BASE_URL}/v2/prices/cheap"
            
            params = {
                "token": self.token,
                "origin": origin,
                "limit": limit
            }
            
            logger.info(f"Getting cheap routes from {origin}")
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            routes = self._parse_cheap_routes(data)
            
            logger.info(f"Found {len(routes)} cheap routes")
            return routes
            
        except requests.exceptions.RequestException as e:
            logger.error(f"TravelPayouts cheap routes error: {str(e)}")
            return []
    
    def search_complex_routes(
        self,
        origins: List[str],
        destination: str,
        departure_date: str,
        return_date: str,
        max_stops: int = 2,
        max_layover_hours: int = 168  # 7 days
    ) -> List[Dict[str, Any]]:
        """Search complex routes with stops in intermediate cities
        
        Args:
            origins: List of departure airports
            destination: Final destination
            departure_date: Departure date
            return_date: Return date
            max_stops: Maximum number of stops
            max_layover_hours: Maximum layover duration in hours (7 days = 168 hours)
            
        Returns:
            List of complex routes
        """
        all_routes = []
        
        for origin in origins:
            try:
                # Search from origin to destination with intermediate stops
                flights = self.search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    max_stops=max_stops
                )
                
                # Filter by layover duration
                valid_flights = [
                    f for f in flights
                    if self._check_layover_duration(f, max_layover_hours)
                ]
                
                all_routes.extend(valid_flights)
                
            except Exception as e:
                logger.error(f"Error searching complex routes from {origin}: {str(e)}")
                continue
        
        return all_routes
    
    def _parse_response(self, data: Dict, max_stops: int) -> List[Dict[str, Any]]:
        """Parse TravelPayouts API response"""
        flights = []
        
        try:
            if not data:
                return flights
            
            # Handle different response formats
            if "data" in data:
                flight_data = data["data"]
            else:
                flight_data = data
            
            if isinstance(flight_data, list):
                for item in flight_data:
                    flight = self._format_flight(item)
                    if flight and self._count_stops(flight) <= max_stops:
                        flights.append(flight)
            elif isinstance(flight_data, dict):
                for key, item in flight_data.items():
                    flight = self._format_flight(item)
                    if flight and self._count_stops(flight) <= max_stops:
                        flights.append(flight)
        
        except Exception as e:
            logger.error(f"Error parsing TravelPayouts response: {str(e)}")
        
        return sorted(flights, key=lambda x: x.get("price", float("inf")))
    
    def _format_flight(self, item: Dict) -> Dict[str, Any]:
        """Format flight data"""
        try:
            return {
                "source": "TravelPayouts",
                "price": item.get("price") or item.get("value"),
                "origin": item.get("origin") or item.get("from"),
                "destination": item.get("destination") or item.get("to"),
                "departure_date": item.get("depart_date") or item.get("departure_date"),
                "return_date": item.get("return_date"),
                "airline": item.get("airline"),
                "duration": item.get("duration"),
                "url": item.get("url") or item.get("link"),
                "stops": self._count_stops(item)
            }
        except Exception as e:
            logger.error(f"Error formatting flight: {str(e)}")
            return None
    
    def _parse_cheap_routes(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse cheap routes response"""
        routes = []
        
        try:
            if isinstance(data, dict):
                for key, item in data.items():
                    route = {
                        "source": "TravelPayouts",
                        "destination": item.get("destination") or item.get("to"),
                        "price": item.get("price") or item.get("value"),
                        "departure_date": item.get("depart_date") or item.get("departure_date"),
                        "duration": item.get("duration"),
                        "url": item.get("url") or item.get("link")
                    }
                    routes.append(route)
        except Exception as e:
            logger.error(f"Error parsing cheap routes: {str(e)}")
        
        return sorted(routes, key=lambda x: x.get("price", float("inf")))
    
    @staticmethod
    def _count_stops(flight: Dict) -> int:
        """Count number of stops in flight"""
        stops = 0
        
        if "stops" in flight:
            return int(flight["stops"])
        
        if "segments" in flight and isinstance(flight["segments"], list):
            return len(flight["segments"]) - 1
        
        return stops
    
    @staticmethod
    def _check_layover_duration(flight: Dict, max_hours: int) -> bool:
        """Check if layover duration is within limits"""
        try:
            if "duration" in flight:
                duration_minutes = flight["duration"]
                duration_hours = duration_minutes / 60 if isinstance(duration_minutes, (int, float)) else 0
                return duration_hours <= max_hours
        except Exception:
            pass
        
        return True
