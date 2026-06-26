"""
Flight search runner using multiple APIs
"""
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from search_engines import TravelPayoutsSearcher, AviasalesSearcher, SkyScannerSearcher
from complex_route_finder import ComplexRouteFinder

logger = logging.getLogger(__name__)


class FlightSearchRunner:
    """Run flight searches across multiple engines"""
    
    # Russian airport codes
    RUSSIAN_AIRPORTS = {
        "SVO": "Sheremetyevo (Москва)",
        "VKO": "Vnukovo (Москва)",
        "DME": "Domodedovo (Москва)",
        "AER": "Anapa",
        "VOZ": "Voronezh",
        "ROV": "Rostov-on-Don",
        "KRR": "Krasnodar",
        "MRV": "Mineralnye Vody"
    }
    
    def __init__(
        self,
        travelpayouts_token: str = None,
        aviasales_token: str = None,
        rapidapi_key: str = None
    ):
        """Initialize flight search runner
        
        Args:
            travelpayouts_token: TravelPayouts API token
            aviasales_token: Aviasales API token
            rapidapi_key: RapidAPI key for SkyScanner
        """
        self.searchers = {}
        self.route_finder = ComplexRouteFinder()
        
        if travelpayouts_token:
            self.searchers["travelpayouts"] = TravelPayoutsSearcher(travelpayouts_token)
            logger.info("Initialized TravelPayouts searcher")
        
        if aviasales_token:
            self.searchers["aviasales"] = AviasalesSearcher(aviasales_token)
            logger.info("Initialized Aviasales searcher")
        
        if rapidapi_key:
            self.searchers["skyscanner"] = SkyScannerSearcher(rapidapi_key)
            logger.info("Initialized SkyScanner searcher")
    
    def search_from_russian_airports(
        self,
        destination: str,
        departure_date: str,
        return_date: str = None,
        airport_codes: List[str] = None,
        max_stops: int = 2
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search flights from Russian airports
        
        Args:
            destination: Destination airport code
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD), optional
            airport_codes: Specific Russian airports to search (default: all)
            max_stops: Maximum number of stops
            
        Returns:
            Dictionary with results grouped by origin airport
        """
        if airport_codes is None:
            airport_codes = list(self.RUSSIAN_AIRPORTS.keys())
        
        results = {}
        
        for airport_code in airport_codes:
            if airport_code not in self.RUSSIAN_AIRPORTS:
                logger.warning(f"Unknown airport code: {airport_code}")
                continue
            
            logger.info(f"Searching from {airport_code}")
            
            flights = []
            
            # Search from each engine
            for engine_name, searcher in self.searchers.items():
                try:
                    if engine_name == "travelpayouts":
                        engine_flights = searcher.search_flights(
                            origin=airport_code,
                            destination=destination,
                            departure_date=departure_date,
                            return_date=return_date,
                            max_stops=max_stops
                        )
                    elif engine_name == "aviasales":
                        engine_flights = searcher.search_flights(
                            origin=airport_code,
                            destination=destination,
                            departure_date=departure_date,
                            return_date=return_date
                        )
                    elif engine_name == "skyscanner":
                        engine_flights = searcher.search_flights(
                            origin=airport_code,
                            destination=destination,
                            departure_date=departure_date,
                            return_date=return_date,
                            max_stops=max_stops
                        )
                    
                    flights.extend(engine_flights)
                    logger.info(f"  {engine_name}: found {len(engine_flights)} flights")
                
                except Exception as e:
                    logger.error(f"Error searching {engine_name} from {airport_code}: {str(e)}")
            
            # Deduplicate and sort
            unique_flights = self._deduplicate(flights)
            unique_flights.sort(key=lambda x: x.get("price", float("inf")))
            results[airport_code] = unique_flights
        
        return results
    
    def search_complex_routes(
        self,
        departure_airports: List[str],
        destination: str,
        departure_date: str,
        return_date: str,
        max_stops: int = 2,
        max_layover_hours: int = 168,
        max_total_duration_hours: int = 504,
        budget: float = None
    ) -> List[Dict[str, Any]]:
        """Search complex routes with stops
        
        Args:
            departure_airports: List of departure airports
            destination: Final destination
            departure_date: Departure date
            return_date: Return date
            max_stops: Maximum stops
            max_layover_hours: Maximum layover duration (hours)
            max_total_duration_hours: Maximum total trip duration (hours)
            budget: Maximum budget in USD
            
        Returns:
            List of complex routes
        """
        logger.info(f"Searching complex routes from {departure_airports} to {destination}")
        
        routes = self.route_finder.find_routes_with_stops(
            search_engines=self.searchers,
            origins=departure_airports,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            max_stops=max_stops,
            max_layover_hours=max_layover_hours,
            max_total_duration_hours=max_total_duration_hours,
            budget=budget
        )
        
        logger.info(f"Found {len(routes)} complex routes")
        return routes
    
    def search_multi_city_itinerary(
        self,
        start_airport: str,
        intermediate_cities: List[str],
        final_destination: str,
        dates: List[str],
        max_budget: float = None
    ) -> List[Dict[str, Any]]:
        """Search multi-city itinerary
        
        Args:
            start_airport: Starting airport
            intermediate_cities: Intermediate cities to visit
            final_destination: Final destination
            dates: Dates for each leg
            max_budget: Maximum budget
            
        Returns:
            List of multi-city itineraries
        """
        logger.info(f"Searching multi-city route: {start_airport} → {' → '.join(intermediate_cities)} → {final_destination}")
        
        itineraries = self.route_finder.find_multi_city_routes(
            search_engines=self.searchers,
            origin=start_airport,
            intermediate_cities=intermediate_cities,
            final_destination=final_destination,
            dates=dates,
            max_budget=max_budget
        )
        
        logger.info(f"Found {len(itineraries)} multi-city itineraries")
        return itineraries
    
    def find_cheapest_flight(
        self,
        departure_airports: List[str],
        destination: str,
        departure_date: str,
        return_date: str = None
    ) -> Dict[str, Any]:
        """Find cheapest flight to destination
        
        Args:
            departure_airports: List of departure airports
            destination: Destination
            departure_date: Departure date
            return_date: Return date, optional
            
        Returns:
            Cheapest flight data
        """
        logger.info(f"Finding cheapest flight from {departure_airports} to {destination}")
        
        cheapest = self.route_finder.find_cheapest_route_to_destination(
            search_engines=self.searchers,
            origins=departure_airports,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date
        )
        
        if cheapest:
            logger.info(f"Cheapest: ${cheapest.get('price')} from {cheapest.get('origin')}")
        
        return cheapest
    
    def search_popular_destinations(self) -> List[Dict[str, Any]]:
        """Get popular destinations from major Russian airports"""
        destinations = []
        
        for airport_code in ["SVO", "VKO", "DME"]:  # Major Moscow airports
            if "aviasales" in self.searchers:
                try:
                    logger.info(f"Getting popular destinations from {airport_code}")
                    popular = self.searchers["aviasales"].get_popular_destinations(airport_code, limit=20)
                    destinations.extend(popular)
                except Exception as e:
                    logger.error(f"Error getting popular destinations: {str(e)}")
            
            if "travelpayouts" in self.searchers:
                try:
                    cheap_routes = self.searchers["travelpayouts"].get_cheap_routes(airport_code, limit=20)
                    destinations.extend(cheap_routes)
                except Exception as e:
                    logger.error(f"Error getting cheap routes: {str(e)}")
        
        # Deduplicate and sort
        unique = self._deduplicate(destinations)
        unique.sort(key=lambda x: x.get("price", float("inf")))
        
        return unique[:50]
    
    @staticmethod
    def _deduplicate(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates from results"""
        seen = set()
        unique = []
        
        for item in items:
            key = (
                item.get("origin"),
                item.get("destination"),
                item.get("departure_date"),
                round(float(item.get("price", 0)))
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(item)
        
        return unique
    
    def get_airports_info(self) -> Dict[str, str]:
        """Get information about Russian airports"""
        return self.RUSSIAN_AIRPORTS


def example_usage():
    """Example of how to use the flight searcher"""
    
    # Initialize with your API keys
    runner = FlightSearchRunner(
        travelpayouts_token="a63fddaa09a757a60d85f48ced731dd7",
        aviasales_token="a63fddaa09a757a60d85f48ced731dd7",
        rapidapi_key="921753dbefmsh9b0467d9eddb199p154cc1jsndaad47aaf922"
    )
    
    # Example 1: Search from Russian airports to a destination
    print("\n=== Search from Russian airports to Bangkok ===")
    results = runner.search_from_russian_airports(
        destination="BKK",
        departure_date="2026-07-20",
        return_date="2026-07-27",
        airport_codes=["SVO", "VKO", "DME"]
    )
    
    for airport, flights in results.items():
        print(f"\n{airport} ({runner.RUSSIAN_AIRPORTS[airport]}):")
        for flight in flights[:3]:  # Show top 3
            print(f"  ${flight['price']} - {flight['source']}")
    
    # Example 2: Find cheapest flight
    print("\n=== Finding cheapest flight ===")
    cheapest = runner.find_cheapest_flight(
        departure_airports=["SVO", "VKO", "DME"],
        destination="IST",
        departure_date="2026-08-01",
        return_date="2026-08-08"
    )
    
    if cheapest:
        print(f"Best deal: ${cheapest.get('price')} from {cheapest.get('origin')} to {cheapest.get('destination')}")
    
    # Example 3: Search complex routes
    print("\n=== Searching complex routes with stops ===")
    complex_routes = runner.search_complex_routes(
        departure_airports=["SVO", "VKO", "DME"],
        destination="MAD",
        departure_date="2026-08-10",
        return_date="2026-08-20",
        max_stops=2,
        budget=1500
    )
    
    print(f"Found {len(complex_routes)} complex routes:")
    for route in complex_routes[:5]:
        print(f"  ${route['price']} - {route['source']}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    example_usage()
