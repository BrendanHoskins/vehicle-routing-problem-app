


def format_solution(data, manager, routing, solution):
    routes = []
    distance_dimension = routing.GetDimensionOrDie("Distance")
    volume_dimension = routing.GetDimensionOrDie("Volume")
    weight_dimension = routing.GetDimensionOrDie("Weight")

    total_cost = 0
    for vehicle_id in range(len(data["trucks"])):
        index = routing.Start(vehicle_id)
        route_distance = 0
        route_stops = []
        route_load_volume = 0
        route_load_weight = 0

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_stops.append(node_index)

            dist_cumul = distance_dimension.CumulVar(index)
            vol_cumul  = volume_dimension.CumulVar(index)
            wt_cumul   = weight_dimension.CumulVar(index)

            previous_index = index
            index = solution.Value(routing.NextVar(index))

            arc_cost = routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            total_cost += arc_cost
            route_distance += arc_cost

        node_index = manager.IndexToNode(index)
        route_stops.append(node_index)

        route_info = {
            "vehicle_id": vehicle_id,
            "truck_identifier": data["trucks"][vehicle_id]["truck_identifier"],
            "stops": route_stops,
            "route_cost": route_distance,
        }
        routes.append(route_info)

    return {
        "routes": routes,
        "objective_value": solution.ObjectiveValue(),
        "total_arc_cost": total_cost,
    }
