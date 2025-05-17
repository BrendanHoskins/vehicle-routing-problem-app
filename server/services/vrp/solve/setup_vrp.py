from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import logging
import sys

from server.services.vrp.callbacks.distance_callback import distance_callback

from server.services.vrp.dimensions.distance_dimension import add_distance_dimension
from server.services.vrp.dimensions.volume_dimension import add_volume_dimension
from server.services.vrp.dimensions.weight_dimension import add_weight_dimension

from server.services.vrp.constraints.pickup_delivery_constraints import add_pickup_delivery_constraints

# Setup logging
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_vrp(csv_data, distance_matrix_data):
    logger.debug("Starting setup_vrp function")
    logger.debug(f"Matrix size: {len(distance_matrix_data['matrix'])}")
    logger.debug(f"Number of trucks: {len(csv_data['trucks'])}")
    logger.debug(f"Vehicle starts: {distance_matrix_data['vehicle_starts']}")
    logger.debug(f"Vehicle ends: {distance_matrix_data['vehicle_ends']}")
    
    # Validate inputs to make sure they match expectations
    if not all(isinstance(idx, int) for idx in distance_matrix_data['vehicle_starts']):
        logger.error("vehicle_starts contains non-integer values")
        # Convert to integers if needed
        distance_matrix_data['vehicle_starts'] = [int(idx) for idx in distance_matrix_data['vehicle_starts']]
    
    if not all(isinstance(idx, int) for idx in distance_matrix_data['vehicle_ends']):
        logger.error("vehicle_ends contains non-integer values")
        # Convert to integers if needed
        distance_matrix_data['vehicle_ends'] = [int(idx) for idx in distance_matrix_data['vehicle_ends']]
    
    try:
        manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix_data["matrix"]),
            len(csv_data["trucks"]),
            distance_matrix_data["vehicle_starts"],
            distance_matrix_data["vehicle_ends"]
        )
        routing = pywrapcp.RoutingModel(manager)
        
        # Add dimensions one by one with error handling
        try:
            add_distance_dimension(routing, manager, csv_data, distance_matrix_data)
            logger.debug("Distance dimension added successfully")
        except Exception as e:
            logger.error(f"Error adding distance dimension: {str(e)}")
            raise
        
        try:
            add_volume_dimension(routing, manager, csv_data, distance_matrix_data)
            logger.debug("Volume dimension added successfully")
        except Exception as e:
            logger.error(f"Error adding volume dimension: {str(e)}")
            raise
        
        try:
            add_weight_dimension(routing, manager, csv_data, distance_matrix_data)
            logger.debug("Weight dimension added successfully")
        except Exception as e:
            logger.error(f"Error adding weight dimension: {str(e)}")
            raise
        
        # --- START: Add penalties for dropping nodes (for debugging) ---
        penalty = 1000000  # A large cost for dropping a node
        skipped_penalty_nodes_count = 0
        added_penalty_nodes_count = 0

        # Iterate through your actual location indices (0 to N-1)
        for matrix_index in range(len(distance_matrix_data["locations"])):
            # Check if this matrix_index is a vehicle start or end node
            is_vehicle_start_or_end = False
            if matrix_index in distance_matrix_data["vehicle_starts"] or \
               matrix_index in distance_matrix_data["vehicle_ends"]:
                is_vehicle_start_or_end = True
            
            # We only add disjunctions for non-start/end nodes that are *supposed* to be visited
            # (i.e., those that would generate demand in your callbacks)
            if not is_vehicle_start_or_end:
                loc_data = distance_matrix_data["locations"][matrix_index]
                node_type = loc_data.get("type", "")
                
                is_demand_node = False
                # Now delivery_current is also a demand node (pickup from depot)
                if node_type == "pickup_current" or \
                   node_type == "pickup_destination" or \
                   node_type == "delivery_destination" or \
                   node_type == "delivery_current":
                    is_demand_node = True

                if is_demand_node:
                    # Convert your matrix_index to the solver's internal index for this node
                    try:
                        solver_node_index = manager.NodeToIndex(matrix_index)
                        routing.AddDisjunction([solver_node_index], penalty)
                        # logger.debug(f"Added disjunction for matrix index {matrix_index} (solver index {solver_node_index}) with penalty {penalty}")
                        added_penalty_nodes_count +=1
                    except Exception as e:
                        # This can happen if a matrix_index is not actually part of the routing model 
                        # (e.g. if it was a duplicate address that got mapped to another index by the manager, though unlikely with your setup)
                        # or if NodeToIndex fails for some other reason.
                        logger.error(f"Could not get solver index for matrix_index {matrix_index} to add disjunction: {e}")
                else:
                    skipped_penalty_nodes_count +=1
            else:
                skipped_penalty_nodes_count +=1
        
        logger.info(f"Disjunctions: Added for {added_penalty_nodes_count} demand nodes, skipped for {skipped_penalty_nodes_count} (vehicle start/end or no-demand) nodes.")
        # --- END: Add penalties for dropping nodes ---
        
        # Try with pickup/delivery constraints, but handle possible errors
        try:
            # TEMPORARILY COMMENTED OUT FOR DEBUGGING INFEASIBILITY
            # add_pickup_delivery_constraints(routing, manager, distance_matrix_data,
            #                               volume_dim_name="Volume",
            #                               weight_dim_name="Weight")
            # logger.debug("Pickup delivery constraints added successfully (SKIPPED FOR DEBUGGING)")
            logger.warning("Pickup delivery constraints SKIPPED FOR DEBUGGING INFEASIBILITY")
        except Exception as e:
            logger.error(f"Error adding pickup delivery constraints: {str(e)}")
            # Continue without these constraints, but log the error
            logger.warning("Continuing without pickup/delivery constraints due to error during their setup.")
        
        logger.debug("Successfully set up VRP model")
        return routing, manager
    except Exception as e:
        logger.error(f"Error in setup_vrp: {e}", exc_info=True)
        raise
