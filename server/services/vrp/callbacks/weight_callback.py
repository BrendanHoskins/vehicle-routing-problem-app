def weight_callback(node_index, distance_matrix_data):
    """
    Return net 'weight' demand at this location.
    - delivery_current: Item is loaded at this depot.
    - delivery_destination: Item is unloaded.
    - pickup_current: Item is picked up.
    - pickup_destination: Item picked up earlier is unloaded here.
    """
    loc = distance_matrix_data["locations"][node_index]
    wt = loc.get("weight", 0.0)
    node_type = loc.get("type", "")

    if node_type == "delivery_current": # Item is LOADED at this depot for this delivery
        return int(+wt)
    elif node_type == "delivery_destination":  # Item is unloaded at customer
        return int(-wt)
    elif node_type == "pickup_current":  # Item is picked up from customer/location
        return int(+wt)
    elif node_type == "pickup_destination":  # Item picked up previously is now dropped at its destination (e.g. another depot/hub)
        return int(-wt)

    return 0