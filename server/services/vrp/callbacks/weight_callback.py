def weight_callback(node_index, distance_matrix_data):
    """
    Return net 'weight' demand at this location.
    Positive => picking up cargo, Negative => dropping off cargo.
    """
    loc = distance_matrix_data["locations"][node_index]
    wt = loc.get("weight", 0.0)
    node_type = loc.get("type", "")
    if "pickup_current" in node_type:
        return int(+wt)  # picking up cargo
    if "delivery_current" in node_type:
        return int(-wt)  # dropping off cargo
    return 0