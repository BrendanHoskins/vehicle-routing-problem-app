from server.services.vrp.callbacks.volume_callback import volume_callback

def add_volume_dimension(routing, manager, csv_data, distance_matrix_data):
    """Add volume dimension with vehicle-specific capacity constraints."""
    vol_cb_index = routing.RegisterUnaryTransitCallback(
        lambda i: volume_callback(manager.IndexToNode(i), distance_matrix_data)
    )
    truck_vol_caps = [int(t["max_volume"]) for t in csv_data["trucks"]]
    routing.AddDimensionWithVehicleCapacity(
        vol_cb_index,
        0,
        truck_vol_caps,
        True,
        "Volume"
    )
