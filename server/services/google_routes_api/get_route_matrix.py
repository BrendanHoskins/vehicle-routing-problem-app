import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

def create_distance_matrix(addresses, depot_indices):
    try:
        API_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not API_key:
            raise Exception("Put your Google Maps API key in .env")

        # Create a mapping of addresses to their metadata
        locations = [
            {
                "address": addr,
                "index": idx,
                "is_depot": idx in depot_indices
            }
            for idx, addr in enumerate(addresses)
        ]

        max_addresses_per_batch = 25
        n = len(addresses)
        distance_matrix = [[0] * n for _ in range(n)]  # Initialize full n×n matrix
        
        # Process all addresses in batches
        for i in range(0, n, max_addresses_per_batch):
            batch_origins = addresses[i:i + max_addresses_per_batch]
            
            # Get distances to all other addresses
            for j in range(0, n, max_addresses_per_batch):
                batch_destinations = addresses[j:j + max_addresses_per_batch]
                response = send_request(batch_origins, batch_destinations, API_key)
                
                if 'error' in response:
                    raise Exception(response['error'].get('message', 'Error in Google Routes API response'))

                batch_matrix = build_distance_matrix(response)
                
                # Copy batch results into the full matrix
                for row_idx, row in enumerate(batch_matrix):
                    for col_idx, value in enumerate(row):
                        distance_matrix[i + row_idx][j + col_idx] = value
        
        return {
            "success": True, 
            "data": {
                "matrix": distance_matrix,
                "locations": locations,
                "depot_indices": depot_indices
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_request(origin_addresses, dest_addresses, API_key):
    """Build and send request using Google Routes API for the given origin and destination addresses."""
    try:
        url = 'https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix'
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_key,
            "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status,condition"
        }
        
        data = {
            "origins": [{"waypoint" : { "address": addr}} for addr in origin_addresses],
            "destinations": [{"waypoint" : {"address": addr}} for addr in dest_addresses],
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE"
        }
        
        print("\n=== Google Routes API Request ===")
        print(f"URL: {url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data)
        
        print("\n=== Google Routes API Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"\nError: {str(e)}")
        return {"error": {"message": f"Request failed: {str(e)}"}}

def build_distance_matrix(response):
    """Build a distance matrix from the Google Routes API response.
    
    Args:
        response (list): List of route elements from the API
        
    Returns:
        list: 2D matrix of distances where matrix[i][j] is the distance from origin i to destination j
    """
    # Find the number of origins and destinations
    max_origin = max(elem['originIndex'] for elem in response) + 1
    max_dest = max(elem['destinationIndex'] for elem in response) + 1
    
    # Initialize the matrix with zeros
    distance_matrix = [[0] * max_dest for _ in range(max_origin)]
    
    # Fill in the distances
    for elem in response:
        i = elem['originIndex']
        j = elem['destinationIndex']
        # If origin and destination are different, use distanceMeters
        # If they're the same, distance is 0 (already set in initialization)
        if i != j and 'distanceMeters' in elem:
            distance_matrix[i][j] = elem['distanceMeters']
    
    return distance_matrix