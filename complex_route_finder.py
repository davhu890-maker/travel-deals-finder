"""
Complex route finder for finding cheapest itineraries with multiple stops
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from itertools import combinations

logger = logging.getLogger(__name__)


class ComplexRouteFinder:
    """Find complex routes with stops in intermediate cities"""
    
    def __init__(self):
        """Initialize complex route finder"""
        self.routes_cache = {}
    
    def find_routes_with_stops(
        self,
        search_engines: Dict[str, Any],
        origins: List[str],
        destination: str,
        departure_date: str,
        return_date: str,
        max_stops: int = 2,
        max_layover_hours: int = 168,
        max_total_duration_hours: int = 504,
        budget: float = None
    ) -> List[Dict[str, Any]]:
        """Find complex routes with possible stops"""
        all_routes = []
        
        if "travelpayouts" in search_engines and search_engines["travelpayouts"]:
            try:
                logger.info("Searching TravelPayouts for complex routes...")
                routes = search_engines["travelpayouts"].search_flights(
                    origin=origins[0] if origins else "SVO",
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    max_stops=max_stops
                )
                all_routes.extend(routes)
            except Exception as e:
                logger.error(f"TravelPayouts complex route search error: {str(e)}")
        
        if "aviasales" in search_engines and search_engines["aviasales"]:
            try:
                logger.info("Searching Aviasales for complex routes...")
                routes = search_engines["aviasales"].search_flights(
                    origin=origins[0] if origins else "SVO",
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date
                )
                all_routes.extend(routes)
            except Exception as e:
                logger.error(f"Aviasales complex route search error: {str(e)}")
        
        if "skyscanner" in search_engines and search_engines["skyscanner"]:
            try:
                logger.info("Searching SkyScanner for complex routes...")
                routes = search_engines["skyscanner"].search_flights(
                    origin=origins[0] if origins else "SVO",
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    max_stops=max_stops
                )
                all_routes.extend(routes)
            except Exception as e:
                logger.error(f"SkyScanner complex route search error: {str(e)}")
        
        unique_routes = self._deduplicate_routes(all_routes)
        
        if budget:
            unique_routes = [r for r in unique_routes if r.get("price", float("inf")) <= budget]
        
        unique_routes.sort(key=lambda x: x.get("price", float("inf")))
        
        logger.info(f"Found {len(unique_routes)} unique complex routes")
        return unique_routes[:100]
    
    def find_cheapest_route_to_destination(
        self,
        search_engines: Dict[str, Any],
        origins: List[str],
        destination: str,
        departure_date: str,
        return_date: str = None,
        consider_indirect: bool = True
    ) -> Dict[str, Any]:
        """Find single cheapest route to destination"""
        all_flights = []
        
        for origin in origins:
            if "travelpayouts" in search_engines and search_engines["travelpayouts"]:
                try:
                    flights = search_engines["travelpayouts"].search_flights(
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        return_date=return_date
                    )
                    all_flights.extend(flights)
                except Exception as e:
                    logger.error(f"Error searching from {origin}: {str(e)}")
            
            if "aviasales" in search_engines and search_engines["aviasales"]:
                try:
                    flights = search_engines["aviasales"].search_flights(
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        return_date=return_date
                    )
                    all_flights.extend(flights)
                except Exception as e:
                    logger.error(f"Error searching from {origin}: {str(e)}")
            
            if "skyscanner" in search_engines and search_engines["skyscanner"]:
                try:
                    flights = search_engines["skyscanner"].search_flights(
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        return_date=return_date
                    )
                    all_flights.extend(flights)
                except Exception as e:
                    logger.error(f"Error searching from {origin}: {str(e)}")
        
        if not consider_indirect:
            all_flights = [f for f in all_flights if f.get("stops", 0) == 0]
        
        if not all_flights:
            logger.warning(f"No flights found to {destination}")
            return {}
        
        all_flights.sort(key=lambda x: x.get("price", float("inf")))
        cheapest = all_flights[0]
        
        logger.info(f"Cheapest route: {cheapest.get('origin')} → {cheapest.get('destination')} for ${cheapest.get('price')}")
        return cheapest
    
    def _deduplicate_routes(self, routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate routes"""
        seen = set()
        unique = []
        
        for route in routes:
            key = (
                route.get("origin"),
                route.get("destination"),
                route.get("departure_date"),
                route.get("return_date"),
                round(float(route.get("price", 0)))
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(route)
        
        return unique