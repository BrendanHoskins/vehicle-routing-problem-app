from server.services.vrp.callbacks.cost_callback import _calculate_fuel_cost, _calculate_labor_cost
import logging

logger = logging.getLogger(__name__)

# Define a global or configurable price per gallon, matching cost_callback.py
PRICE_PER_GALLON = 3.5 

def add_total_cost_dimension_and_evaluator(routing, manager, processed_csv_data, distance_matrix_data_actual):
    """
    Sets the primary arc cost evaluator for the routing model based on fuel and labor.
    Also adds a 'TotalCost' dimension to track cumulative costs (optional but good for inspection).
    """

    num_vehicles = len(processed_csv_data["trucks"])

    # Prepare employee data: map truck_identifier to hourly_rate
    truck_to_employee_rate = {}
    if 'employees' in processed_csv_data:
        for emp in processed_csv_data['employees']:
            # Assuming one employee per truck for simplicity, or you might average/sum if multiple
            if emp.get('truck_uid') and emp.get('truck_uid') != "N/A":
                truck_to_employee_rate[emp['truck_uid']] = emp.get('hourly_pay_rate', 0.0)
    
    logger.debug(f"Truck to employee rate map: {truck_to_employee_rate}")

    # Create and register a transit callback for each vehicle
    # This is necessary because fuel (MPG) and labor (employee assigned to truck) are vehicle-specific.
    for vehicle_id in range(num_vehicles):
        truck_info = processed_csv_data["trucks"][vehicle_id]
        truck_identifier = truck_info["truck_identifier"]
        truck_mpg = truck_info.get("mpg", 1.0) # Default to 1 MPG if not specified
        if truck_mpg <= 0: # Ensure MPG is positive
            logger.warning(f"Truck {truck_identifier} has invalid MPG {truck_mpg}, defaulting to 1.0 for cost calculation.")
            truck_mpg = 1.0

        employee_hourly_rate = truck_to_employee_rate.get(truck_identifier, 0.0)
        if employee_hourly_rate == 0.0:
            logger.warning(f"No employee or 0 hourly rate found for truck {truck_identifier}, labor cost will be 0 for this truck.")

        def vehicle_specific_arc_cost_callback(from_index_solver, to_index_solver,
                                              # Capture vehicle-specific data in closure
                                              current_truck_mpg=truck_mpg, 
                                              current_hourly_rate=employee_hourly_rate):
            from_node_matrix = manager.IndexToNode(from_index_solver)
            to_node_matrix = manager.IndexToNode(to_index_solver)

            distance_m = distance_matrix_data_actual['distance_matrix'][from_node_matrix][to_node_matrix]
            duration_s = distance_matrix_data_actual['time_matrix'][from_node_matrix][to_node_matrix]

            fuel_c = _calculate_fuel_cost(distance_m, current_truck_mpg, PRICE_PER_GALLON)
            labor_c = _calculate_labor_cost(duration_s, current_hourly_rate)
            
            total_c = fuel_c + labor_c
            
            # OR-Tools expects integer costs. Scale if necessary (e.g., multiply by 100 if dealing with cents)
            # For now, let's assume costs are significant enough to be integers, or can be rounded.
            # logger.debug(f"Cost for veh {vehicle_id} ({from_node_matrix}->{to_node_matrix}): dist={distance_m}, time={duration_s}, mpg={current_truck_mpg}, rate={current_hourly_rate} => fuel={fuel_c:.2f}, labor={labor_c:.2f}, total={int(total_c)}")
            return int(round(total_c)) # Round to nearest integer

        # Register this vehicle-specific callback
        # The lambda captures the current vehicle_id for logging, and vehicle_specific_arc_cost_callback captures mpg/rate
        
        # Create a lambda that correctly captures the current vehicle's data for the callback
        # Need to be careful with late binding in loops if not using default arguments for lambda.
        
        # Correct way to create unique callbacks for each vehicle
        cost_callback_index = routing.RegisterTransitCallback(
            (lambda mpg=truck_mpg, rate=employee_hourly_rate: 
                lambda from_solver, to_solver: vehicle_specific_arc_cost_callback(from_solver, to_solver, mpg, rate)
            )() # Immediately call the outer lambda to bind current mpg and rate
        )
        routing.SetArcCostEvaluatorOfVehicle(cost_callback_index, vehicle_id)
        logger.debug(f"Set vehicle-specific arc cost evaluator for vehicle_id: {vehicle_id} (Truck: {truck_identifier}) with MPG: {truck_mpg}, Rate: {employee_hourly_rate}")

    logger.info("Successfully set up vehicle-specific arc cost evaluators based on fuel and labor.")

    # Optional: Add a 'TotalCost' dimension to track cumulative cost if desired.
    # This would use the same callbacks.
    # routing.AddDimension(
    #     # Need to re-register callbacks or use a list of callback_indices if they were stored
    #     # For simplicity, if you need a 'TotalCost' dimension, ensure its evaluator
    #     # correctly reflects the vehicle-specific costs.
    #     # This example focuses on setting the primary cost evaluator.
    #     # callback_indices_list[vehicle_id], 
    #     0, # No slack
    #     999999999, # Large upper bound for cumulative cost
    #     True, # Start cumul at zero
    #     "TotalCost"
    # )
    # logger.info("Optional: A 'TotalCost' dimension could be added here if needed for tracking.")
