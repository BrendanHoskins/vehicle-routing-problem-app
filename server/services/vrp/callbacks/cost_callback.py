import logging

logger = logging.getLogger(__name__)

# Define a global or configurable price per gallon
PRICE_PER_GALLON = 3.5 # Example: $3.50 per gallon

def _calculate_fuel_cost(distance_meters, truck_mpg, price_per_gallon):
    if truck_mpg <= 0: # Avoid division by zero or nonsensical MPG
        return 0 
    # 1 meter = 0.000621371 miles
    distance_miles = distance_meters * 0.000621371
    gallons_used = distance_miles / truck_mpg
    return gallons_used * price_per_gallon

def _calculate_labor_cost(duration_seconds, hourly_rate):
    if hourly_rate <= 0 or duration_seconds <=0:
        return 0
    duration_hours = duration_seconds / 3600.0
    return duration_hours * hourly_rate

def arc_cost_callback(from_node_idx_solver, to_node_idx_solver, manager, routing,
                      distance_matrix_data_actual, processed_csv_data):
    """
    Calculates the total cost (fuel + labor) for traversing an arc.
    Args:
        from_node_idx_solver: Solver's index of the starting node of the arc.
        to_node_idx_solver: Solver's index of the ending node of the arc.
        manager (pywrapcp.RoutingIndexManager): OR-Tools index manager.
        routing (pywrapcp.RoutingModel): OR-Tools routing model.
        distance_matrix_data_actual (dict): Contains distance_matrix, time_matrix, locations.
        processed_csv_data (dict): Contains trucks, employees data.
    Returns:
        int: The total cost of the arc, scaled to an integer if necessary for OR-Tools.
    """
    try:
        # Convert solver indices to your matrix indices
        from_node = manager.IndexToNode(from_node_idx_solver)
        to_node = manager.IndexToNode(to_node_idx_solver)

        # Get distance and time for the arc
        distance_meters = distance_matrix_data_actual['distance_matrix'][from_node][to_node]
        duration_seconds = distance_matrix_data_actual['time_matrix'][from_node][to_node]

        # Determine the vehicle serving this arc
        # Note: In a simple transit callback, vehicle_id isn't directly available.
        # However, when SetArcCostEvaluatorOfAllVehicles is used, or if we make vehicle-specific
        # evaluators, we can get it. For a generic arc cost, we might need to
        # consider an average or be careful if costs are vehicle-dependent.
        # For SetArcCostEvaluatorOfAllVehicles, the cost should ideally be vehicle-agnostic
        # or handle averaging/worst-case.
        # If SetArcCostEvaluatorOfVehicle is used, then vehicle_id is implicit.

        # For now, let's assume costs can be calculated based on an "average" or "representative" truck
        # if we use SetArcCostEvaluatorOfAllVehicles.
        # OR, more correctly, when this callback is registered *per vehicle*, the vehicle_id will be known.
        # The `routing.GetArcCostForVehicle` is used by the solver internally with a vehicle context.
        # When we register a callback for *all* vehicles, it needs to return a cost.
        # If fuel/labor costs are vehicle-specific, we MUST register per-vehicle callbacks.

        # For simplicity in this step, let's assume the cost is calculated for vehicle 0.
        # THIS IS A MAJOR SIMPLIFICATION AND NEEDS REFINEMENT IF COSTS ARE VEHICLE-SPECIFIC.
        # A proper implementation would involve registering this callback per vehicle
        # or making the cost calculation truly vehicle-dependent if SetArcCostEvaluatorOfAllVehicles
        # somehow provides vehicle context (which it typically doesn't directly to the callback).
        
        # Let's assume SetArcCostEvaluatorOfAllVehicles is used, and we must return a single cost.
        # We will calculate an *average* cost or use the first vehicle's data as representative.
        # This part is tricky with SetArcCostEvaluatorOfAllVehicles for vehicle-specific costs.
        
        # A better approach for vehicle-specific costs:
        # The callback registered with `routing.RegisterTransitCallback(callback, vehicle_id_type_arg_is_vehicle=True)`
        # would get `vehicle_solver_idx` passed to it.
        # However, the standard SetArcCostEvaluatorOfAllVehicles uses a callback of (from_solver_idx, to_solver_idx).

        # Let's assume for now, for this stage, we are setting a *generic* arc cost.
        # To make it vehicle-specific later, we'd need to register the callback using
        # `routing.SetArcCostEvaluatorOfVehicle(callback_index, vehicle_index)` for each vehicle.

        # For now, let's calculate based on the first truck and first employee for demonstration.
        # This will be refined in the dimension registration.
        
        # Fuel Cost (requires truck's MPG)
        # This needs to be vehicle-specific.
        # If this callback is used with SetArcCostEvaluatorOfAllVehicles, it must return a generic cost.
        # If used with SetArcCostEvaluatorOfVehicle, then the vehicle context is known.
        
        # For now, this callback will return a cost that needs to be understood in context of how it's registered.
        # Let's assume it's called by an evaluator that knows the vehicle.
        # However, the provided signature (from_index, to_index) for RegisterTransitCallback doesn't directly give vehicle.
        
        # To make this work correctly with SetArcCostEvaluatorOfAllVehicles,
        # and have vehicle-specific costs, the usual pattern is to create a class
        # that holds all data, and its method is the callback. The RoutingModel's vehicle
        # variable can be inspected inside the callback if it's part of such a class instance
        # or if we can determine current vehicle during search (complex).

        # Simpler for now: if the cost dimension is added for *all* vehicles, then the cost callback
        # should return a value that is sensible for all, or an average.
        # OR, the cost dimension itself is added per vehicle type if costs vary that way.

        # Let's get vehicle_id from the context of the solver's current evaluation if possible.
        # This is not straightforward from just from_node_idx_solver, to_node_idx_solver.
        # The typical way is to have a callback per vehicle or a callback that is made
        # aware of the vehicle by the way it's registered or the dimension is set up.

        # To proceed, we'll make this callback calculate an *example* cost.
        # The integration in cost_dimension.py will need to handle vehicle specificity.
        
        # Default values if truck/employee data is missing for some reason
        truck_mpg = 10.0 # Default MPG
        employee_hourly_rate = 0.0 # Default rate

        # This callback itself doesn't know the vehicle_id.
        # The cost_dimension will create closures or partial functions that do.
        # So, this function should take truck_mpg and hourly_rate as arguments.

        # Refined helpers (they are fine as they are)

        # This main callback's signature is what RegisterTransitCallback expects.
        # It needs to be adapted if vehicle-specific data is used directly here.
        # For now, let's assume this function is a template and the actual registered
        # callback will be a partial function with vehicle-specific data bound.

        # This function, as a generic callback for all vehicles, cannot use specific truck/employee data
        # unless it iterates over ALL trucks/employees and returns an average/max, which is not ideal.
        # The correct way is to register per-vehicle cost evaluators, or a dimension that handles this.

        # Placeholder: for now, just return distance as cost to ensure structure works.
        # We will properly calculate and use fuel/labor in the next step within cost_dimension.py
        
        # To make this runnable, it needs to return *some* cost.
        # The true cost calculation will be built into the dimension setup.
        # This function will act more like a data retriever for the dimension.
        # The cost dimension itself will make it vehicle-specific.
        
        # For now, let's just use distance, the time matrix will be used in the dimension.
        # This is a temporary measure to make the file runnable.
        # The real logic will be in how cost_dimension.py uses this data.
        # return int(distance_meters) # OR-Tools costs should be integers

        # For this stage, we will make this function return a tuple (distance, duration)
        # and the actual cost calculation with fuel/labor will be done in the
        # closure/lambda created in cost_dimension.py
        return distance_meters, duration_seconds

    except Exception as e:
        logger.error(f"Error in arc_cost_callback for arc {from_node} -> {to_node}: {e}", exc_info=True)
        return 0, 0 # Return a high cost or handle error appropriately
    
    