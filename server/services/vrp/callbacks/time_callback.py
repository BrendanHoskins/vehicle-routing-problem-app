import logging

logger = logging.getLogger(__name__)

# Define default service times in seconds
DEFAULT_SERVICE_TIME_SECONDS = 600  # 10 minutes
DEPOT_SERVICE_TIME_SECONDS = 300     # 5 minutes for depot interactions like loading

def get_service_time_seconds(node_matrix_index, distance_matrix_data_actual):
    """
    Returns the service time for a given node.
    Customize this based on node type or specific data.
    """
    try:
        location_info = distance_matrix_data_actual['locations'][node_matrix_index]
        node_type = location_info.get('type', '')

        if 'depot' in node_type or 'delivery_current' in node_type : # delivery_current is a depot load
            return DEPOT_SERVICE_TIME_SECONDS
        elif 'delivery_destination' in node_type or \
             'pickup_current' in node_type or \
             'pickup_destination' in node_type:
            return DEFAULT_SERVICE_TIME_SECONDS
        # Truck start/end nodes typically have 0 service time unless specific setup/wrap-up is modeled
        elif 'truck' in node_type or 'truck_end' in node_type:
            return 0
        else:
            return 0 # Default for unknown types or nodes without specific service needs
    except IndexError:
        logger.error(f"Node matrix index {node_matrix_index} out of bounds for locations data.")
        return DEFAULT_SERVICE_TIME_SECONDS # Fallback
    except Exception as e:
        logger.error(f"Error getting service time for node {node_matrix_index}: {e}")
        return DEFAULT_SERVICE_TIME_SECONDS # Fallback

def travel_time_plus_service_callback(from_node_idx_solver, to_node_idx_solver, manager, distance_matrix_data_actual):
    """
    Returns the travel time + service time for the 'to_node'.
    This is a common pattern for time dimensions where service occurs upon arrival.
    """
    try:
        from_node_matrix = manager.IndexToNode(from_node_idx_solver)
        to_node_matrix = manager.IndexToNode(to_node_idx_solver)

        travel_time_seconds = distance_matrix_data_actual['time_matrix'][from_node_matrix][to_node_matrix]
        service_time_at_to_node_seconds = get_service_time_seconds(to_node_matrix, distance_matrix_data_actual)
        
        # logger.debug(f"TimeCB: Arc {from_node_matrix}->{to_node_matrix}, Travel: {travel_time_seconds}s, Service at {to_node_matrix}: {service_time_at_to_node_seconds}s")
        return travel_time_seconds + service_time_at_to_node_seconds
    except Exception as e:
        logger.error(f"Error in travel_time_plus_service_callback for arc from solver idx {from_node_idx_solver} to {to_node_idx_solver}: {e}", exc_info=True)
        # Return a very large time if error, or handle appropriately
        return 9999999 # Indicate an issue 