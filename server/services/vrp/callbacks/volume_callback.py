
def volume_callback(node_index, distance_matrix_data):
    """
    Return net 'volume' demand at this location.
    Positive => picking up cargo, Negative => dropping off cargo.
    """
    loc = distance_matrix_data["locations"][node_index]
    # If location is a pickup => +volume
    # If location is a delivery => -volume
    vol = loc.get("volume", 0.0)
    node_type = loc.get("type", "")
    if "pickup_current" in node_type:
        return int(+vol)  # picking up cargo
    if "delivery_current" in node_type:
        return int(-vol)  # dropping off cargo
    return 0