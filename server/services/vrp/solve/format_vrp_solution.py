import logging

logger = logging.getLogger(__name__)

def format_solution(processed_csv_data, distance_matrix_data_actual, manager, routing, solution):
    """
    Formats the VRP solution.
    Args:
        processed_csv_data (dict): The original CSV data.
        distance_matrix_data_actual (dict): The data part of distance_matrix_data, 
                                            containing 'locations', 'matrix', etc.
        manager (pywrapcp.RoutingIndexManager): The OR-Tools index manager.
        routing (pywrapcp.RoutingModel): The OR-Tools routing model.
        solution (pywrapcp.Assignment): The solution object from the solver.
    """
    routes = []
    # Ensure dimensions exist before trying to Get them, or handle potential errors
    try:
        distance_dimension = routing.GetDimensionOrDie("Distance")
    except Exception:
        logger.warning("Distance dimension not found in routing model.")
        distance_dimension = None
    
    try:
        volume_dimension = routing.GetDimensionOrDie("Volume")
    except Exception:
        logger.warning("Volume dimension not found in routing model.")
        volume_dimension = None

    try:
        weight_dimension = routing.GetDimensionOrDie("Weight")
    except Exception:
        logger.warning("Weight dimension not found in routing model.")
        weight_dimension = None

    try:
        time_dimension = routing.GetDimensionOrDie("Time")
    except Exception:
        logger.warning("Time dimension not found in routing model.")
        time_dimension = None

    total_objective_cost = solution.ObjectiveValue() # This includes penalties if nodes were dropped
    total_route_arc_cost = 0 # This will be the sum of actual travel distances

    visited_matrix_indices = set()

    for vehicle_id in range(len(processed_csv_data["trucks"])):
        index = routing.Start(vehicle_id)
        route_distance = 0
        route_stops_matrix_indices = [] # Store matrix indices for this route
        
        # Store full location details for stops if available
        route_stops_details = []


        current_load_volume = 0
        current_load_weight = 0

        while not routing.IsEnd(index):
            node_matrix_index = manager.IndexToNode(index)
            route_stops_matrix_indices.append(node_matrix_index)
            visited_matrix_indices.add(node_matrix_index)
            
            # Get location details
            loc_detail = next((loc for loc in distance_matrix_data_actual['locations'] if loc['index'] == node_matrix_index), None)
            
            stop_info = {
                "matrix_index": node_matrix_index,
                "address": loc_detail['address'] if loc_detail else "N/A",
                "type": loc_detail['type'] if loc_detail else "N/A",
                "identifier": loc_detail.get('identifier', 'N/A')
            }
            if distance_dimension:
                stop_info["distance_cumul"] = solution.Value(distance_dimension.CumulVar(index))
            if volume_dimension:
                stop_info["volume_cumul"] = solution.Value(volume_dimension.CumulVar(index))
            if weight_dimension:
                stop_info["weight_cumul"] = solution.Value(weight_dimension.CumulVar(index))
            if time_dimension:
                stop_info["time_cumul_seconds"] = solution.Value(time_dimension.CumulVar(index))
            
            route_stops_details.append(stop_info)


            previous_index = index
            index = solution.Value(routing.NextVar(index))
            
            # Arc cost contributes to route_distance and total_route_arc_cost
            # but not necessarily to the objective if penalties are involved.
            arc_cost = routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            route_distance += arc_cost
            total_route_arc_cost += arc_cost


        # Add the end node of the route
        end_node_matrix_index = manager.IndexToNode(index)
        route_stops_matrix_indices.append(end_node_matrix_index)
        visited_matrix_indices.add(end_node_matrix_index)
        
        loc_detail_end = next((loc for loc in distance_matrix_data_actual['locations'] if loc['index'] == end_node_matrix_index), None)
        stop_info_end = {
            "matrix_index": end_node_matrix_index,
            "address": loc_detail_end['address'] if loc_detail_end else "N/A",
            "type": loc_detail_end['type'] if loc_detail_end else "N/A",
            "identifier": loc_detail_end.get('identifier', 'N/A')
        }
        if distance_dimension:
            stop_info_end["distance_cumul"] = solution.Value(distance_dimension.CumulVar(index))
        if volume_dimension:
            stop_info_end["volume_cumul"] = solution.Value(volume_dimension.CumulVar(index))
        if weight_dimension:
            stop_info_end["weight_cumul"] = solution.Value(weight_dimension.CumulVar(index))
        if time_dimension:
            stop_info_end["time_cumul_seconds"] = solution.Value(time_dimension.CumulVar(index))
        route_stops_details.append(stop_info_end)


        route_info = {
            "vehicle_id": vehicle_id,
            "truck_identifier": processed_csv_data["trucks"][vehicle_id]["truck_identifier"],
            "stops_matrix_indices": route_stops_matrix_indices, # List of matrix indices
            "stops_details": route_stops_details, # List of detailed stop info
            "route_cost_distance": route_distance, # Actual travel distance for this route
        }

        # Check if the vehicle is effectively unused (only start and end nodes visited, and no "work" done)
        # A vehicle is unused if its route_stops_matrix_indices contains only its start and end node,
        # and no other unique nodes from the mandatory_node_types.
        # A simpler check: if number of distinct stops (excluding start/end if they are the only ones) is 0.
        # Or, if the route consists of exactly 2 stops which are the vehicle's start and end.
        
        # Get the vehicle's defined start and end matrix indices
        vehicle_start_node_idx = distance_matrix_data_actual["vehicle_starts"][vehicle_id]
        vehicle_end_node_idx = distance_matrix_data_actual["vehicle_ends"][vehicle_id]

        # A vehicle is considered "unused" if its route consists only of its start and end node,
        # and no other intermediate service stops.
        # The route_stops_matrix_indices will always contain at least the start and end node.
        is_unused = False
        if len(route_stops_matrix_indices) == 2 and \
           route_stops_matrix_indices[0] == vehicle_start_node_idx and \
           route_stops_matrix_indices[1] == vehicle_end_node_idx:
            is_unused = True
        # Handle case where start and end are the same, and it's the only stop (effectively unused)
        # Note: route_stops_matrix_indices will have [start_node, start_node] if start=end and no tasks
        elif vehicle_start_node_idx == vehicle_end_node_idx and \
             len(route_stops_matrix_indices) == 2 and \
             route_stops_matrix_indices[0] == vehicle_start_node_idx and \
             route_stops_matrix_indices[1] == vehicle_start_node_idx : # Both stops are the same start/end node
             is_unused = True
        # A more robust check might involve seeing if any "task" nodes were visited.
        # Let's count non-start/end nodes in the route.
        num_actual_task_stops = 0
        for stop_idx_in_route in route_stops_matrix_indices:
            if stop_idx_in_route != vehicle_start_node_idx and stop_idx_in_route != vehicle_end_node_idx:
                # Further check if this stop_idx_in_route is one of the 'task' types if needed
                # For now, any intermediate stop means it's used.
                # However, depots are intermediate but not tasks.
                # Let's refine: check if any of the mandatory_node_types were visited by this truck.
                is_task_node_in_route = False
                for stop_detail in route_stops_details: # Iterate through detailed stops for this route
                    # Exclude the first (start) and last (end) stops from this specific check if they match vehicle's own start/end
                    is_current_stop_vehicle_start = (stop_detail['matrix_index'] == vehicle_start_node_idx and route_stops_details.index(stop_detail) == 0)
                    is_current_stop_vehicle_end = (stop_detail['matrix_index'] == vehicle_end_node_idx and route_stops_details.index(stop_detail) == len(route_stops_details)-1)

                    if not is_current_stop_vehicle_start and not is_current_stop_vehicle_end:
                        # Check against the defined mandatory node types
                        # These are the types for which disjunctions were added
                        defined_mandatory_node_types = [ 
                            "delivery_current", "delivery_destination", 
                            "pickup_current", "pickup_destination"
                        ]
                        if stop_detail['type'] in defined_mandatory_node_types:
                            is_task_node_in_route = True
                            break 
                if not is_task_node_in_route: # If after checking all stops, no task node was found for this vehicle
                    is_unused = True # Re-evaluate this logic: if is_task_node_in_route is false for whole route, then unused.

        # Simpler check for "unused": if the route length is 2 (start, end) and no "task" was done
        # A vehicle did "work" if it visited any node other than its own start/end,
        # OR if its start/end are different and it traveled.
        # The clearest indicator is if it visited any of the "mandatory_node_types"
        
        # Revised Unused Check:
        # A vehicle is considered unused if its route contains no nodes of type
        # "delivery_current", "delivery_destination", "pickup_current", "pickup_destination".
        # (Except if the start/end node itself is one of these, which is an edge case we're not focusing on for "unused")
        
        has_serviced_mandatory_task = False
        # Check stops between the absolute start and absolute end of the vehicle's journey
        for i in range(len(route_stops_details)):
            stop_detail = route_stops_details[i]
            # If it's the first stop and it's the vehicle's start, or last stop and vehicle's end, skip unless it's also a task
            is_true_vehicle_start_stop = (i == 0 and stop_detail['matrix_index'] == vehicle_start_node_idx)
            is_true_vehicle_end_stop = (i == len(route_stops_details) - 1 and stop_detail['matrix_index'] == vehicle_end_node_idx)

            # A node is a service task if its type is one of the mandatory types
            # AND it's not *just* the vehicle's own start or end depot being transited through.
            # However, a vehicle start/end *can* be a service location.
            # The key is if *any* node of these types is in the route.
            defined_mandatory_node_types = [ 
                "delivery_current", "delivery_destination", 
                "pickup_current", "pickup_destination"
            ]
            if stop_detail['type'] in defined_mandatory_node_types:
                has_serviced_mandatory_task = True
                break
        
        route_info["is_used"] = has_serviced_mandatory_task
        if not has_serviced_mandatory_task:
            logger.info(f"Vehicle {vehicle_id} (Truck: {route_info['truck_identifier']}) is considered UNUSED as it serviced no mandatory task types.")


        routes.append(route_info)

    # Identify unvisited mandatory nodes (those that should have had a disjunction)
    unvisited_mandatory_nodes = []
    if routing.GetNumberOfDisjunctions() > 0: # Check if disjunctions were active
        mandatory_node_types = [
            "delivery_current", 
            "delivery_destination", 
            "pickup_current", 
            "pickup_destination"
        ]
        for loc in distance_matrix_data_actual['locations']:
            matrix_idx = loc['index']
            # Exclude vehicle start/end nodes from this check, even if they overlap with a depot address
            is_vehicle_start_node = matrix_idx in distance_matrix_data_actual.get("vehicle_starts", [])
            is_vehicle_end_node = matrix_idx in distance_matrix_data_actual.get("vehicle_ends", [])

            if loc['type'] in mandatory_node_types and \
               not is_vehicle_start_node and \
               not is_vehicle_end_node and \
               matrix_idx not in visited_matrix_indices:
                unvisited_mandatory_nodes.append({
                    "matrix_index": matrix_idx,
                    "identifier": loc.get("identifier"),
                    "type": loc.get("type"),
                    "address": loc.get("address")
                })
        if unvisited_mandatory_nodes:
            logger.warning(f"Found {len(unvisited_mandatory_nodes)} unvisited mandatory nodes (penalties likely paid):")
            for unvisited_node in unvisited_mandatory_nodes:
                logger.warning(f"  - Index: {unvisited_node['matrix_index']}, ID: {unvisited_node['identifier']}, Type: {unvisited_node['type']}, Addr: {unvisited_node['address']}")


    return {
        "routes": routes,
        "objective_value": total_objective_cost, # Includes penalties
        "total_route_arc_cost": total_route_arc_cost, # Sum of distances traveled
        "unvisited_mandatory_nodes": unvisited_mandatory_nodes
    }
