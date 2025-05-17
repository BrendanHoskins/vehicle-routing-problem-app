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
        route_stops_details.append(stop_info_end)


        route_info = {
            "vehicle_id": vehicle_id,
            "truck_identifier": processed_csv_data["trucks"][vehicle_id]["truck_identifier"],
            "stops_matrix_indices": route_stops_matrix_indices, # List of matrix indices
            "stops_details": route_stops_details, # List of detailed stop info
            "route_cost_distance": route_distance, # Actual travel distance for this route
        }
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
