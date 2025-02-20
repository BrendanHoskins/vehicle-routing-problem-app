from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from services.google_routes_api.get_route_matrix import create_distance_matrix
from services.vrp.callbacks.distance_callback import distance_callback
from services.vrp.dimensions.distance_dimension import add_distance_dimension
from services.csv.process_csv_file import process_selected_columns

def setup_vrp(data):
    distance_matrix_response = create_distance_matrix(data['addresses'], data['depot'])
    
    if not distance_matrix_response['success']:
        raise Exception(distance_matrix_response['error'])

    matrix_data = distance_matrix_response["data"]
    data["distance_matrix"] = matrix_data["matrix"]
    data["locations"] = matrix_data["locations"]
    data["depot_indices"] = matrix_data["depot_indices"]

    if len(data["depot"]) == 1:
        manager = pywrapcp.RoutingIndexManager(
            len(data["distance_matrix"]), data["num_vehicles"], data["depot"][0]
        )
    else:
        manager = pywrapcp.RoutingIndexManager(
            len(data["distance_matrix"]), data["num_vehicles"], data["depot"], data["depot"]
        )

    routing = pywrapcp.RoutingModel(manager)

    transit_callback = lambda from_index, to_index: distance_callback(
        from_index, to_index, manager, data
    )
    transit_callback_index = routing.RegisterTransitCallback(transit_callback)

    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    add_distance_dimension(routing, transit_callback_index)

    return manager, routing

def solve_vrp(data):
    try:
        processed_data = process_selected_columns(data['csv_data'])

        if processed_data is None:
            return {"success": False, "error": "Failed to process CSV data - no data returned"}

        data['addresses'] = processed_data['addresses']
        if not processed_data['addresses']:
            return {"success": False, "error": "No valid addresses found in CSV data"}

        if processed_data['depot_indices']:
            data['depot'] = processed_data['depot_indices']
        else:
            return {"success": False, "error": "No depot location found in CSV data"}

        manager, routing = setup_vrp(data)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            result = format_solution(data, manager, routing, solution)
            return {"success": True, "data": result}
        return {"success": False, "error": "No solution found for the given VRP problem"}

    except Exception as e:
        return {
            "success": False,
            "error": f"Error solving VRP: {str(e)}",
            "error_type": type(e).__name__
        }

def format_solution(data, manager, routing, solution):
    routes = []
    max_route_distance = 0

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = {
            "vehicle_id": vehicle_id,
            "stops": [],
            "stop_details": [],
            "distance": 0
        }

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route["stops"].append(node_index)
            route["stop_details"].append({
                "index": node_index,
                "address": data["locations"][node_index]["address"],
                "is_depot": data["locations"][node_index]["is_depot"]
            })
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route["distance"] += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )

        node_index = manager.IndexToNode(index)
        route["stops"].append(node_index)
        route["stop_details"].append({
            "index": node_index,
            "address": data["locations"][node_index]["address"],
            "is_depot": data["locations"][node_index]["is_depot"]
        })
        
        routes.append(route)
        max_route_distance = max(route["distance"], max_route_distance)

    return {
        "routes": routes,
        "objective_value": solution.ObjectiveValue(),
        "max_route_distance": max_route_distance,
        "locations": data["locations"]
    }
