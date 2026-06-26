"""
SkyScanner API search engine via RapidAPI
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import time

logger = logging.getLogger(__name__)


class SkyScannerSearcher:
    """Search flights using SkyScanner API through RapidAPI"""
    
    BASE_URL = "https://skyscanner-api.p.rapidapi.com"
    
    def __init__(self, rapidapi_key: str):
        """Initialize SkyScanner searcher
        
        Args:
            rapidapi_key: RapidAPI key for SkyScanner
        """
        self.rapidapi_key = rapidapi_key
        self.headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "skyscanner-api.p.rapidapi.com"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str = None,
        adults: int = 1,
        max_stops: int = None
    ) -> List[Dict[str, Any]]:
        """Search for flights
        
        Args:
            origin: IATA code of departure airport
            destination: IATA code of destination airport
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD), optional
            adults: Number of adults
            max_stops: Maximum number of stops (None for any)
            
        Returns:
            List of flight deals
        """
        try:
            endpoint = f"{self.BASE_URL}/v1/search"
            
            params = {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "adults": adults,
                "currency": "USD"
            }
            
            logger.info(f"Searching SkyScanner: {origin} → {destination} ({departure_date})")
            response = self.session.get(endpoint, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            flights = self._parse_response(data, max_stops)
            
            logger.info(f"Found {len(flights)} flights from SkyScanner")
            return flights
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SkyScanner search error: {str(e)}")
            return []
    
    def _parse_response(self, data: Dict, max_stops: int = None) -> List[Dict[str, Any]]:
        """Parse search response"""
        flights = []
        
        try:
            if not data:
                return flights
            
            if "quotes" in data:
                for quote in data["quotes"]:
                    flight = self._format_quote(quote)
                    if flight:
                        if max_stops is not None and flight.get("stops", 0) > max_stops:
                            continue
                        flights.append(flight)
            
            if "results" in data:
                for item in data["results"]:
                    flight = self._format_result(item)
                    if flight:
                        if max_stops is not None and flight.get("stops", 0) > max_stops:
                            continue
                        flights.append(flight)
        
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
        
        return sorted(flights, key=lambda x: x.get("price", float("inf")))
    
    def _format_quote(self, item: Dict) -> Dict[str, Any]:
        """Format quote data"""
        try:
            price = item.get("MinPrice") or item.get("price") or item.get("Value")
            if not price:
                return None
            
            return {
                "source": "SkyScanner",
                "price": price,
                "origin": item.get("OriginId") or item.get("origin"),
                "destination": item.get("DestinationId") or item.get("destination"),
                "departure_date": item.get("OutboundDateTime") or item.get("departure_date"),
                "return_date": item.get("InboundDateTime") or item.get("return_date"),
                "direct": item.get("Direct"),
                "url": item.get("DeeplinkUrl") or item.get("url"),
                "stops": 0 if item.get("Direct") else 1
            }
        except Exception as e:
            logger.error(f"Error formatting quote: {str(e)}")
            return None
    
    def _format_result(self, item: Dict) -> Dict[str, Any]:
        """Format result data"""
        try:
            price = item.get("MinPrice") or item.get("price")
            if not price:
                return None
            
            return {
                "source": "SkyScanner",
                "price": price,
                "origin": item.get("Origin"),
                "destination": item.get("Destination"),
                "departure_date": item.get("OutboundLegsDirect"),
                "direct": item.get("Direct"),
                "url": item.get("DeeplinkUrl") or item.get("url"),
                "stops": 0 if item.get("Direct") else 1
            }
        except Exception as e:
            logger.error(f"Error formatting result: {str(e)}")
            return None