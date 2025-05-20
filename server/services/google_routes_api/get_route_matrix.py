import requests
import json
import time
from dotenv import load_dotenv
import os
from collections import deque

load_dotenv()

# We'll track past requests in a rolling 60-second window
# Each entry is a tuple: (timestamp, element_count)
REQUESTS_LOG = deque()

# Load cache from disk if it exists
CACHE_FILE = os.path.join(os.path.dirname(__file__), "distance_cache.json")
try:
    with open(CACHE_FILE, 'r') as f:
        content = f.read().strip()
        if content:
            serialized_cache = json.loads(content)
            # Convert string keys back to tuples
            DISTANCE_CACHE = {tuple(k.split('|||')): v for k, v in serialized_cache.items()}
        else:
            DISTANCE_CACHE = {}
except (FileNotFoundError, json.JSONDecodeError):
    DISTANCE_CACHE = {}
    # Initialize the cache file with an empty dictionary
    with open(CACHE_FILE, 'w') as f:
        json.dump({}, f)

def save_cache():
    """
    Save the distance cache to disk.
    NOTE: Ensure your environment (e.g., container) persists 
    this file across runs, otherwise you'll lose your cache.
    """
    # Convert tuple keys to strings for JSON serialization
    serializable_cache = {f"{o}|||{d}": v for (o, d), v in DISTANCE_CACHE.items()}
    with open(CACHE_FILE, 'w') as f:
        json.dump(serializable_cache, f)

def normalize_address(address):
    """
    Basic normalization for addresses to ensure consistent caching.
    Adjust to your own needs (remove punctuation, standardize abbreviations, etc.)
    """
    if not address:
        return ''
    return address.strip().lower()

def create_distance_matrix(deliveries, depots, trucks, pickups):
    """
    Build distance and time matrices using deliveries, depots, trucks, and pickups data.

    Args:
        deliveries (list): List of deliveries, each with:
          {
            "identifier": str,
            "current_location": str,
            "destination": str,
            "volume": float,
            "weight": float,
          }

        depots (list): List of depots, each with:
          {
            "identifier": str,
            "location": str
          }

        trucks (list): List of trucks, each with:
          {
            "truck_identifier": str,
            "max_volume": float,
            "max_weight": float,
            "current_location": str,
            "end_location": str,
            "range": float
          }

        pickups (list): List of pickups, each with:
          {
            "identifier": str,
            "current_location": str,
            "destination": str,
            "volume": float,
            "weight": float,
          }

    Returns:
        dict: {
            "success": bool,
            "data" or "error": Dictionary
        }

        On success:
            {
                "success": True,
                "data": {
                    "distance_matrix": 2D list of distances (in meters),
                    "time_matrix": 2D list of durations (in seconds),
                    "locations": [metadata for each address],
                    "depot_indices": [indices of depots in the matrix],
                    "vehicle_starts": [indices of truck current locations],
                    "vehicle_ends": [indices of truck end locations]
                }
            }

        On error:
            {
                "success": False,
                "error": str
            }
    """
    try:
        API_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not API_key:
            raise Exception("Put your Google Maps API key in .env (GOOGLE_MAPS_API_KEY)")

        # Instead of a single index per address string, let's incorporate a "role suffix"
        # so that the same address with different roles becomes unique in the matrix:
        unique_addresses = []
        address_to_index = {}

        def get_address_index(raw_address, role_suffix=""):
            """
            Combine the address string + role suffix into a key.
            That way, the same physical address + different role becomes a distinct index.
            """
            norm_addr = normalize_address(raw_address)
            key = (norm_addr, role_suffix)
            if key not in address_to_index:
                address_to_index[key] = len(unique_addresses)
                # Store just the normalized *address* or the entire key. Here we store address only:
                unique_addresses.append(norm_addr)
            return address_to_index[key]

        locations = []
        truck_current_indices = []
        truck_end_indices = []

        # ----- 1) Process trucks -----
        for truck in trucks:
            # Create distinct indices for the truck start & end, even if they share the address
            current_idx = get_address_index(truck["current_location"],
                                            role_suffix=f"truck_start_{truck['truck_identifier']}")
            end_idx = get_address_index(truck["end_location"],
                                        role_suffix=f"truck_end_{truck['truck_identifier']}")

            truck_current_indices.append(current_idx)
            truck_end_indices.append(end_idx)

            # Record metadata for the start location
            locations.append({
                "address": normalize_address(truck["current_location"]),
                "index": current_idx,
                "identifier": truck["truck_identifier"],
                "type": "truck",
                "max_volume": truck["max_volume"],
                "max_weight": truck["max_weight"],
                "range": truck["range"]
            })
            # Record metadata for the end location
            locations.append({
                "address": normalize_address(truck["end_location"]),
                "index": end_idx,
                "identifier": truck["truck_identifier"],
                "type": "truck_end"
            })

        # ----- 2) Process depots -----
        for depot in depots:
            # Single role suffix for all depots or incorporate their identifier if you prefer
            depot_idx = get_address_index(depot["location"],
                                          role_suffix=f"depot_{depot['identifier']}")
            locations.append({
                "address": normalize_address(depot["location"]),
                "index": depot_idx,
                "identifier": depot["identifier"],
                "type": "depot"
            })

        # ----- 3) Process deliveries -----
        for delivery in deliveries:
            current_idx = get_address_index(delivery["current_location"],
                                            role_suffix=f"delivery_current_{delivery['identifier']}")
            dest_idx = get_address_index(delivery["destination"],
                                         role_suffix=f"delivery_destination_{delivery['identifier']}")
            locations.append({
                "address": normalize_address(delivery["current_location"]),
                "index": current_idx,
                "identifier": delivery["identifier"],
                "type": "delivery_current",
                "volume": delivery["volume"],
                "weight": delivery["weight"]
            })
            locations.append({
                "address": normalize_address(delivery["destination"]),
                "index": dest_idx,
                "identifier": delivery["identifier"],
                "type": "delivery_destination",
                "volume": delivery["volume"],
                "weight": delivery["weight"]
            })

        # ----- 4) Process pickups -----
        for pickup in pickups:
            current_idx = get_address_index(pickup["current_location"],
                                            role_suffix=f"pickup_current_{pickup['identifier']}")
            dest_idx = get_address_index(pickup["destination"],
                                         role_suffix=f"pickup_destination_{pickup['identifier']}")
            locations.append({
                "address": normalize_address(pickup["current_location"]),
                "index": current_idx,
                "identifier": pickup["identifier"],
                "type": "pickup_current",
                "volume": pickup["volume"],
                "weight": pickup["weight"]
            })
            locations.append({
                "address": normalize_address(pickup["destination"]),
                "index": dest_idx,
                "identifier": pickup["identifier"],
                "type": "pickup_destination",
                "volume": pickup["volume"],
                "weight": pickup["weight"]
            })

        # Now create the master distance and time matrices (n x n):
        n = len(unique_addresses)
        distance_matrix = [[0] * n for _ in range(n)]
        time_matrix = [[0] * n for _ in range(n)]

        # We'll batch requests to Google depending on your usage
        max_origins_per_batch = 25
        max_destinations_per_batch = 25

        for i in range(0, n, max_origins_per_batch):
            batch_origins = unique_addresses[i:i + max_origins_per_batch]

            for j in range(0, n, max_destinations_per_batch):
                batch_destinations = unique_addresses[j:j + max_destinations_per_batch]

                num_elements = len(batch_origins) * len(batch_destinations)
                throttle(num_elements)

                response = cached_send_request(batch_origins, batch_destinations, API_key)
                if "error" in response:
                    raise Exception(response["error"].get("message", "Google Routes API error"))

                batch_dist_matrix, batch_time_matrix = extract_matrices_from_response(response)
                for row_idx, row_data in enumerate(batch_dist_matrix):
                    for col_idx, value in enumerate(row_data):
                        distance_matrix[i + row_idx][j + col_idx] = value
                
                for row_idx, row_data in enumerate(batch_time_matrix):
                    for col_idx, value in enumerate(row_data):
                        time_matrix[i + row_idx][j + col_idx] = value

        return {
            "success": True,
            "data": {
                "distance_matrix": distance_matrix,
                "time_matrix": time_matrix,
                "locations": locations,
                "depot_indices": [loc["index"] for loc in locations if loc["type"] == "depot"],
                "vehicle_starts": truck_current_indices,
                "vehicle_ends": truck_end_indices
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def throttle(num_elements):
    """
    Enforce the "3000 elements per minute" rate limit.
    We keep a rolling 60-second window of requests in REQUESTS_LOG.
    Each entry is (timestamp, element_count). If adding 'num_elements'
    would exceed 3000 in the last 60 seconds, we wait until it doesn't.
    """
    now = time.time()
    # First, prune entries older than 60 seconds
    while REQUESTS_LOG and (now - REQUESTS_LOG[0][0] > 60):
        REQUESTS_LOG.popleft()

    # Calculate how many elements have been used in the last 60s
    used = sum(e for _, e in REQUESTS_LOG)
    # If adding the new request would exceed 3000, we wait
    while used + num_elements > 3000:
        time.sleep(1)
        now = time.time()
        # Prune again after sleeping
        while REQUESTS_LOG and (now - REQUESTS_LOG[0][0] > 60):
            REQUESTS_LOG.popleft()
        used = sum(e for _, e in REQUESTS_LOG)

    # Now we can proceed
    REQUESTS_LOG.append((time.time(), num_elements))

def cached_send_request(origins, destinations, api_key):
    """
    Check in-memory cache for existing origin->destination distances.
    For any not found, fetch from Google and update the cache.
    """
    missing_origins = []
    missing_destinations = []
    origin_indices = {}
    dest_indices = {}

    for i, o in enumerate(origins):
        norm_o = normalize_address(o)
        for j, d in enumerate(destinations):
            norm_d = normalize_address(d)
            if (norm_o, norm_d) not in DISTANCE_CACHE:
                if i not in origin_indices:
                    origin_indices[i] = len(missing_origins)
                    missing_origins.append(norm_o)
                if j not in dest_indices:
                    dest_indices[j] = len(missing_destinations)
                    missing_destinations.append(norm_d)

    # If everything is in cache, we can build a synthetic response
    if not missing_origins or not missing_destinations:
        return build_response_from_cache(origins, destinations)

    # Request only the missing pairs
    response = send_request(missing_origins, missing_destinations, api_key)

    # If it's an error, return it
    if 'error' in response:
        return response

    # Update cache with new values
    for elem in response:
        o_idx = elem["originIndex"]
        d_idx = elem["destinationIndex"]
        dist_meters = elem.get("distanceMeters", 0)
        
        duration_str = elem.get("duration", "0s") # e.g., "123s"
        duration_seconds = 0
        if duration_str and duration_str.endswith('s'):
            try:
                duration_seconds = int(duration_str[:-1])
            except ValueError:
                duration_seconds = 0 # Default if parsing fails
        
        origin_addr = missing_origins[o_idx]
        dest_addr = missing_destinations[d_idx]
        DISTANCE_CACHE[(origin_addr, dest_addr)] = {
            "distance_meters": dist_meters,
            "duration_seconds": duration_seconds
        }

    # Save cache to disk
    save_cache()

    return build_response_from_cache(origins, destinations)

def build_response_from_cache(origins, destinations):
    """
    Construct a 'fake' API response from cached data only.
    Return it in the same shape as the actual API response, e.g.
      [
        {"originIndex": 0, "destinationIndex": 0, "distanceMeters": ...},
        ...
      ]
    """
    response = []
    for i, o in enumerate(origins):
        norm_o = normalize_address(o)
        for j, d in enumerate(destinations):
            norm_d = normalize_address(d)
            cached_data = DISTANCE_CACHE.get((norm_o, norm_d))
            
            dist_meters = 0
            duration_seconds = 0

            if isinstance(cached_data, dict): # New format
                dist_meters = cached_data.get("distance_meters", 0)
                duration_seconds = cached_data.get("duration_seconds", 0)
            elif isinstance(cached_data, (int, float)): # Potentially old format (just distance)
                # This case should ideally not happen if cache is cleared after format change
                # Or if new entries always use the dict format.
                # If we encounter this, it means this pair is missing duration.
                # We might want to force a re-fetch for this pair, but for now,
                # we'll proceed with 0 duration and log a warning.
                # A better strategy if this occurs would be to treat this item as not fully cached.
                dist_meters = int(cached_data)
                duration_seconds = 0 # No duration info in old format
                # Consider logging a warning here if you expect all cache entries to be dicts
                # print(f"Warning: Cache item for ({norm_o}, {norm_d}) is in old format. Duration will be 0.")
            
            response.append({
                "originIndex": i,
                "destinationIndex": j,
                "distanceMeters": dist_meters,
                "duration": f"{duration_seconds}s" # Mimic API response format
            })
    return response

def send_request(origin_addresses, dest_addresses, API_key):
    """
    Build and send request to Google Routes API with exponential backoff handling errors.
    """
    url = 'https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix'
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_key,
        "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status,condition"
    }
    data = {
        "origins": [{"waypoint": {"address": addr}} for addr in origin_addresses],
        "destinations": [{"waypoint": {"address": addr}} for addr in dest_addresses],
        "travelMode": "DRIVE"
    }

    # Exponential backoff parameters
    max_retries = 5
    backoff_delay = 1  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n=== Attempt {attempt}/{max_retries} ===")
            print("Sending Google Routes API Request...")
            print(f"URL: {url}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Data: {json.dumps(data, indent=2)}")

            response = requests.post(url, headers=headers, json=data)
            print(f"Status Code: {response.status_code}")

            try:
                # Attempt to parse JSON if possible
                parsed = response.json()
                print(f"Response JSON: {json.dumps(parsed, indent=2)}")
            except Exception:
                print("Response is not valid JSON; raw text:")
                print(response.text)
                parsed = {"error": {"message": "Response is not valid JSON"}}

            response.raise_for_status()
            return parsed

        except requests.exceptions.HTTPError as http_err:
            if response.status_code in [429, 500, 502, 503, 504]:
                if attempt < max_retries:
                    wait_time = backoff_delay * (2 ** (attempt - 1))
                    print(f"Got {response.status_code}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {"error": {"message": f"Max retries reached for status {response.status_code}: {str(http_err)}"}}
            else:
                return {"error": {"message": str(http_err)}}

        except requests.exceptions.RequestException as req_err:
            if attempt < max_retries:
                wait_time = backoff_delay * (2 ** (attempt - 1))
                print(f"RequestException. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                return {"error": {"message": f"Request failed after {attempt} attempts: {str(req_err)}"}}

    return {"error": {"message": "Failed to send request after max retries"}}

def extract_matrices_from_response(response):
    """
    Convert the list of route results from the Google Routes API 
    into a 2D distance matrix and a 2D time matrix.
    """
    if not response:
        return [[]], [[]]

    # Determine matrix dimensions from the response
    # Response elements have originIndex and destinationIndex
    max_origin_idx = -1
    max_dest_idx = -1
    for elem in response:
        if "originIndex" in elem: # Check if key exists
            max_origin_idx = max(max_origin_idx, elem["originIndex"])
        if "destinationIndex" in elem: # Check if key exists
            max_dest_idx = max(max_dest_idx, elem["destinationIndex"])
    
    # If no valid indices found, return empty matrices
    if max_origin_idx == -1 or max_dest_idx == -1:
        # This case can happen if the response is an error object or unexpected format
        # or if all items were from cache and build_response_from_cache had an issue.
        # For safety, determine size from actual indices present if possible.
        # If response is just an error dict:
        if not isinstance(response, list) or not all(isinstance(el, dict) for el in response):
             return [[]], [[]] # Not a list of dicts
        
        # If response is a list but empty or no valid indices
        if not any("originIndex" in elem and "destinationIndex" in elem for elem in response):
            return [[]], [[]]


    num_origins = max_origin_idx + 1
    num_destinations = max_dest_idx + 1

    batch_dist_matrix = [[0] * num_destinations for _ in range(num_origins)]
    batch_time_matrix = [[0] * num_destinations for _ in range(num_origins)]

    for elem in response:
        # Ensure element is a dictionary and has the required keys
        if not isinstance(elem, dict) or "originIndex" not in elem or "destinationIndex" not in elem:
            # Log or handle malformed element if necessary
            continue

        i = elem["originIndex"]
        j = elem["destinationIndex"]
        
        if "distanceMeters" in elem:
            batch_dist_matrix[i][j] = elem["distanceMeters"]
        
        duration_str = elem.get("duration", "0s") # e.g., "123s"
        if duration_str and isinstance(duration_str, str) and duration_str.endswith('s'):
            try:
                batch_time_matrix[i][j] = int(duration_str[:-1])
            except ValueError:
                batch_time_matrix[i][j] = 0 # Default if parsing fails
        elif isinstance(duration_str, (int, float)): # If it's already a number (e.g. from a direct calculation)
             batch_time_matrix[i][j] = int(duration_str)


    return batch_dist_matrix, batch_time_matrix

def deduplicate_addresses(deliveries, depots, trucks):
    """
    Return (unique_addresses, locations_metadata)

    unique_addresses: A simple list of unique address strings.
    locations_metadata: A list of dicts (one per item) with:
        {
          'id': original_item_identifier,
          'type': 'delivery_current' / 'truck' / etc.
          'unique_idx': index_of_deduplicated_address,
          other_keys...
        }
    """
    address_index_map = {}
    unique_addresses = []
    locations_metadata = []

    def get_uni_idx(address):
        """Assign or retrieve a stable index for 'address', with normalization."""
        norm_addr = normalize_address(address)
        if norm_addr not in address_index_map:
            address_index_map[norm_addr] = len(unique_addresses)
            unique_addresses.append(norm_addr)
        return address_index_map[norm_addr]

    # 1. Process trucks
    for truck in trucks:
        uni_idx = get_uni_idx(truck["current_location"])
        locations_metadata.append({
            "id": truck["truck_identifier"],
            "type": "truck",
            "unique_idx": uni_idx,
            "max_volume": truck["max_volume"],
            "max_weight": truck["max_weight"],
            "range": truck["range"],
        })

    # 2. Process depots
    for depot in depots:
        uni_idx = get_uni_idx(depot["location"])
        locations_metadata.append({
            "id": depot["identifier"],
            "type": "depot",
            "unique_idx": uni_idx
        })

    # 3. Process deliveries
    for delivery in deliveries:
        current_uni_idx = get_uni_idx(delivery["current_location"])
        destination_uni_idx = get_uni_idx(delivery["destination"])

        locations_metadata.append({
            "id": delivery["identifier"],
            "type": "delivery_current",
            "volume": delivery["volume"],
            "weight": delivery["weight"],
            "unique_idx": current_uni_idx
        })
        locations_metadata.append({
            "id": delivery["identifier"],
            "type": "delivery_destination",
            "volume": delivery["volume"],
            "weight": delivery["weight"],
            "unique_idx": destination_uni_idx
        })

    return unique_addresses, locations_metadata