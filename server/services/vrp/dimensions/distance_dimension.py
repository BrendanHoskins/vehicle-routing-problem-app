from server.services.vrp.callbacks.distance_callback import distance_callback


def add_distance_dimension(routing, manager, csv_data, distance_matrix_data):
    """Add distance dimension with vehicle-specific range constraints."""

    dist_cb_index = routing.RegisterTransitCallback(
        lambda from_i, to_i: distance_callback(from_i, to_i, manager, distance_matrix_data)
    )
    routing.SetArcCostEvaluatorOfAllVehicles(dist_cb_index)
    # Convert float ranges to integers
    truck_ranges = [int(t["range"]) for t in csv_data['trucks']]

    # TEMPORARILY SETTING VERY LARGE RANGES TO DEBUG INFEASIBILITY
    # This effectively disables the range constraint.
    # Number of vehicles is len(csv_data['trucks'])
    # num_vehicles = len(csv_data['trucks'])
    # A very large number, greater than any possible sum of distances in the matrix.
    # Max distance in your matrix seems to be around 60k, max nodes 64. Max path ~64*60k = ~3.8M
    # Let's use something safely larger.
    # very_large_range = [10**9] * num_vehicles # 1 billion meters

    routing.AddDimensionWithVehicleCapacity(
        dist_cb_index,
        0,                # slack
        truck_ranges,     # vehicle capacities (now using actual ranges)
        True,            # start cumul at zero
        "Distance"
    )
