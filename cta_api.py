"""
CTA Train Tracker API Client
"""
from datetime import datetime
from typing import Optional, List, Dict
import requests
from dateutil import parser as dateparser
from requests.exceptions import RequestException


class CTAClient:
    """Client for fetching CTA train arrival data."""
    
    def __init__(self, api_key: str, stop_id: str):
        """
        Initialize CTA API client.
        
        Args:
            api_key: CTA API key
            stop_id: Station stop ID (e.g., "30254" for Paulina → Loop)
        """
        self.api_key = api_key
        self.stop_id = stop_id
        self.base_url = "http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx"
    
    def get_next_trains(self, route: str = "Brn", destination: str = "loop", max_results: int = 2) -> Optional[List[Dict]]:
        """
        Fetch upcoming trains for a specific route and destination.
        
        Args:
            route: Route code (default: "Brn" for Brown Line)
            destination: Destination keyword to filter (default: "loop")
            max_results: Maximum number of trains to return
        
        Returns:
            List of train dicts with keys: minutes, is_scheduled, is_delayed
            Returns None if API call fails
        """
        params = {
            "key": self.api_key,
            "stpid": self.stop_id,
            "max": max_results,
            "outputType": "JSON",
        }
        
        try:
            r = requests.get(self.base_url, params=params, timeout=10)
            r.raise_for_status()
        except RequestException as e:
            print(f"Error talking to CTA API: {e}")
            return None
        
        try:
            data = r.json()
            etas = data["ctatt"]["eta"]
        except Exception as e:
            print(f"Error parsing CTA API response: {e}")
            return None
        
        now = datetime.now()
        trains = []
        
        for eta in etas:
            # Filter by route
            if eta.get("rt") != route:
                continue
            
            # Filter by destination
            dest = eta.get("destNm", "").lower()
            if destination.lower() not in dest:
                continue
            
            # Parse arrival time
            try:
                arr = dateparser.parse(eta["arrT"])
            except Exception:
                continue
            
            # Calculate minutes until arrival
            diff = int((arr - now).total_seconds() // 60)
            if diff < 0:
                continue
            
            trains.append({
                "minutes": diff,
                "is_scheduled": str(eta.get("isSch", "0")) == "1",
                "is_delayed": str(eta.get("isDly", "0")) == "1",
            })
        
        trains.sort(key=lambda t: t["minutes"])
        return trains[:max_results]