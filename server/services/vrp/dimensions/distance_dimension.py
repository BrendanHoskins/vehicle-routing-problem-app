def add_distance_dimension(routing, transit_callback_index, max_distance=3000):
    """Adds distance dimension to the routing model."""
    dimension_name = "Distance"
    routing.AddDimension(
        transit_callback_index,
        0,
        100000000, 
        True, 
        dimension_name,
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)
    return distance_dimension
