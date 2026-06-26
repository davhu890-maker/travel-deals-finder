"""
Aviasales API search engine for finding cheap flights
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)


class AviasalesSearcher:
    """Search flights using Aviasales API"""
    
    BASE_URL = "https://api.aviasales.ru"
    
    def __init__(self, token: str):
        """Initialize Aviasales searcher
        
        Args:
            token: Aviasales API token
        """
        self.token = token
        self.session = requests.Session()
        
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str = None,
        adults: int = 1
    ) -> List[Dict[str, Any]]:
        """Search for flights
        
        Args:
            origin: IATA code of departure airport
            destination: IATA code of destination airport
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD), optional
            adults: Number of adults
            
        Returns:
            List of flight deals
        """
        try:
            endpoint = f"{self.BASE_URL}/v1/prices"
            
            params = {
                "origin": origin,
                "destination": destination,
                "depart_date": departure_date,
                "return_date": return_date,
                "adults": adults,
                "currency": "USD"
            }
            
            logger.info(f"Searching Aviasales: {origin} → {destination} ({departure_date})")
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            flights = self._parse_response(data)
            
            logger.info(f"Found {len(flights)} flights from Aviasales")
            return flights
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Aviasales search error: {str(e)}")
            return []
    
    def _parse_response(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse Aviasales API response"""
        flights = []
        
        try:
            if "prices" in data:
                for item in data["prices"]:
                    flight = self._format_flight(item)
                    if flight:
                        flights.append(flight)
            elif isinstance(data, list):
                for item in data:
                    flight = self._format_flight(item)
                    if flight:
                        flights.append(flight)
        
        except Exception as e:
            logger.error(f"Error parsing Aviasales response: {str(e)}")
        
        return sorted(flights, key=lambda x: x.get("price", float("inf")))
    
    def _format_flight(self, item: Dict) -> Dict[str, Any]:
        """Format flight data"""
        try:
            price = item.get("price") or item.get("value")
            if not price:
                return None
            
            return {
                "source": "Aviasales",
                "price": price,
                "origin": item.get("origin") or item.get("from"),
                "destination": item.get("destination") or item.get("to"),
                "departure_date": item.get("depart_date") or item.get("departure_date"),
                "return_date": item.get("return_date"),
                "airline": item.get("airline") or item.get("airlines"),
                "duration": item.get("duration"),
                "url": item.get("url") or item.get("link"),
                "stops": item.get("stops", 0)
            }
        except Exception as e:
            logger.error(f"Error formatting flight: {str(e)}")
            return None