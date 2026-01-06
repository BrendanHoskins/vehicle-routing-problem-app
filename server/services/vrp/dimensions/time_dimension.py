from server.services.vrp.callbacks.time_callback import travel_time_plus_service_callback
import logging

logger = logging.getLogger(__name__)

DEFAULT_MAX_SHIFT_DURATION_SECONDS = 12 * 3600 # Default 12 hours if specific employee data is missing

def add_time_dimension(routing, manager, processed_csv_data, distance_matrix_data_actual):
    """Adds a time dimension to the routing model to track route durations and enforce work shifts."""

    # Create a mapping from truck_identifier to employee shift details
    truck_employee_shifts = {}
    if 'employees' in processed_csv_data:
        for emp in processed_csv_data['employees']:
            truck_uid = emp.get('truck_uid')
            start_s = emp.get('work_start_seconds')
            end_s = emp.get('work_end_seconds')
            if truck_uid and truck_uid != "N/A" and start_s is not None and end_s is not None:
                if end_s < start_s: # Handles overnight shifts if needed, or flags invalid data
                    logger.warning(f"Employee {emp.get('employee_uid')} for truck {truck_uid} has end time before start time. Adjusting or assuming next day not handled yet.")
                    # For now, assume it's an error or a simple duration within a day
                    duration = DEFAULT_MAX_SHIFT_DURATION_SECONDS 
                else:
                    duration = end_s - start_s
                
                truck_employee_shifts[truck_uid] = {
                    "start_seconds": start_s,
                    "end_seconds": end_s,
                    "max_duration_seconds": duration
                }
    logger.debug(f"Truck employee shifts: {truck_employee_shifts}")


    # Register the transit callback for time (travel + service)
    # This callback is generic; vehicle-specific constraints are applied via vehicle capacities / cumul vars.
    time_evaluator_index = routing.RegisterTransitCallback(
        lambda from_solver, to_solver: travel_time_plus_service_callback(
            from_solver, to_solver, manager, distance_matrix_data_actual
        )
    )

    dimension_name = "Time"
    routing.AddDimension(
        time_evaluator_index,
        0,  # Slack (waiting time allowed at nodes, can be 0 if tight)
        DEFAULT_MAX_SHIFT_DURATION_SECONDS * len(processed_csv_data["trucks"]), # Global upper bound (sum of all possible shifts - very loose)
        False,  # Start cumul to zero is False, will be set per vehicle
        dimension_name
    )
    time_dimension = routing.GetDimensionOrDie(dimension_name)

    # Set vehicle-specific start and end times and overall duration limits
    for vehicle_id in range(len(processed_csv_data["trucks"])):
        truck_identifier = processed_csv_data["trucks"][vehicle_id]["truck_identifier"]
        shift_info = truck_employee_shifts.get(truck_identifier)

        start_node_solver_idx = routing.Start(vehicle_id)
        end_node_solver_idx = routing.End(vehicle_id)

        if shift_info:
            vehicle_shift_start_seconds = shift_info["start_seconds"]
            vehicle_shift_end_seconds = shift_info["end_seconds"]
            # Set the cumulative time at the start node for this vehicle
            time_dimension.CumulVar(start_node_solver_idx).SetRange(
                vehicle_shift_start_seconds, vehicle_shift_end_seconds # Can start anytime within its shift start window
            )
            # Set the cumulative time at the end node for this vehicle
            time_dimension.CumulVar(end_node_solver_idx).SetRange(
                vehicle_shift_start_seconds, vehicle_shift_end_seconds 
            )
            # Set the maximum total duration (span) for this vehicle's route
            time_dimension.SetSpanUpperBoundForVehicle(shift_info["max_duration_seconds"], vehicle_id)
            logger.info(f"Vehicle {vehicle_id} (Truck: {truck_identifier}): Time window [{vehicle_shift_start_seconds}s - {vehicle_shift_end_seconds}s], Max duration: {shift_info['max_duration_seconds']}s")

        else:
            # Default if no specific shift info for the truck
            time_dimension.CumulVar(start_node_solver_idx).SetRange(0, DEFAULT_MAX_SHIFT_DURATION_SECONDS)
            time_dimension.CumulVar(end_node_solver_idx).SetRange(0, DEFAULT_MAX_SHIFT_DURATION_SECONDS)
            time_dimension.SetSpanUpperBoundForVehicle(DEFAULT_MAX_SHIFT_DURATION_SECONDS, vehicle_id)
            logger.warning(f"Vehicle {vehicle_id} (Truck: {truck_identifier}): No specific shift info, using default time window [0s - {DEFAULT_MAX_SHIFT_DURATION_SECONDS}s]")
            
    logger.info("Time dimension added with vehicle work shift constraints.") 