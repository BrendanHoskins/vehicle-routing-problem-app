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
        
        # Try with pickup/delivery constraints, but handle possible errors
        try:
            add_pickup_delivery_constraints(routing, manager, distance_matrix_data,
                                          volume_dim_name="Volume",
                                          weight_dim_name="Weight")
            logger.debug("Pickup delivery constraints added successfully")
        except Exception as e:
            logger.error(f"Error adding pickup delivery constraints: {str(e)}")
            # Continue without these constraints, but log the error
            logger.warning("Continuing without pickup/delivery constraints")
        
        logger.debug("Successfully set up VRP model")
        return routing, manager
    except Exception as e:
        logger.error(f"Error in setup_vrp: {e}", exc_info=True)
        raise
