from server.services.vrp.callbacks.distance_callback import distance_callback


def add_distance_dimension(routing, manager, csv_data, distance_matrix_data):
    """Add distance dimension with vehicle-specific range constraints."""

    dist_cb_index = routing.RegisterTransitCallback(
        lambda from_i, to_i: distance_callback(from_i, to_i, manager, distance_matrix_data)
    )
    routing.SetArcCostEvaluatorOfAllVehicles(dist_cb_index)
    # Convert float ranges to integers
    truck_ranges = [int(t["range"]) for t in csv_data['trucks']]
    routing.AddDimensionWithVehicleCapacity(
        dist_cb_index,
        0,                # slack
        truck_ranges,     # vehicle capacities
        True,            # start cumul at zero
        "Distance"
    )
