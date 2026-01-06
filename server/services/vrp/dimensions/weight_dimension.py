from server.services.vrp.callbacks.weight_callback import weight_callback

def add_weight_dimension(routing, manager, csv_data, distance_matrix_data):
    """Add weight dimension with vehicle-specific capacity constraints."""
    wt_cb_index = routing.RegisterUnaryTransitCallback(
        lambda i: weight_callback(manager.IndexToNode(i), distance_matrix_data)
    )
    truck_wt_caps = [int(t["max_weight"]) for t in csv_data["trucks"]]
    routing.AddDimensionWithVehicleCapacity(
        wt_cb_index,
        0,
        truck_wt_caps,
        True,
        "Weight"
    )
