def volume_callback(node_index, distance_matrix_data):
    """
    Return net 'volume' demand at this location.
    - delivery_current: Item is LOADED at this depot for this delivery
    - delivery_destination: Item is unloaded at customer
    - pickup_current: Item is picked up from customer/location
    - pickup_destination: Item picked up previously is now dropped at its destination (e.g. another depot/hub)
    """
    loc = distance_matrix_data["locations"][node_index]
    vol = loc.get("volume", 0.0)
    node_type = loc.get("type", "")

    if node_type == "delivery_current": # Item is LOADED at this depot for this delivery
        return int(+vol) 
    elif node_type == "delivery_destination":  # Item is unloaded at customer
        return int(-vol)
    elif node_type == "pickup_current":  # Item is picked up from customer/location
        return int(+vol)
    elif node_type == "pickup_destination":  # Item picked up previously is now dropped at its destination (e.g. another depot/hub)
        return int(-vol)
    
    return 0