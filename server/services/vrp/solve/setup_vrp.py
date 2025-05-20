from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import logging
import sys

from server.services.vrp.callbacks.distance_callback import distance_callback
from server.services.vrp.dimensions.distance_dimension import add_distance_dimension
from server.services.vrp.dimensions.volume_dimension import add_volume_dimension
from server.services.vrp.dimensions.weight_dimension import add_weight_dimension
from server.services.vrp.constraints.pickup_delivery_constraints import add_pickup_delivery_constraints
from server.services.vrp.dimensions.cost_dimension import add_total_cost_dimension_and_evaluator

# Setup logging
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_vrp(csv_data, distance_matrix_data):
    logger.debug("Starting setup_vrp function")
    # distance_matrix_data is now distance_matrix_data_actual (the "data" sub-dictionary)
    # Let's rename it here for clarity to match what's passed.
    distance_matrix_data_actual = distance_matrix_data 

    logger.debug(f"Matrix size (distance): {len(distance_matrix_data_actual['distance_matrix'])}")
    if 'time_matrix' in distance_matrix_data_actual:
        logger.debug(f"Matrix size (time): {len(distance_matrix_data_actual['time_matrix'])}")
    else:
        logger.error("Time matrix is missing from distance_matrix_data_actual!")
        raise ValueError("Time matrix is required for cost calculations but not found.")
        
    logger.debug(f"Number of trucks: {len(csv_data['trucks'])}")
    logger.debug(f"Vehicle starts: {distance_matrix_data_actual['vehicle_starts']}")
    logger.debug(f"Vehicle ends: {distance_matrix_data_actual['vehicle_ends']}")
    
    # Validate inputs to make sure they match expectations
    if not all(isinstance(idx, int) for idx in distance_matrix_data_actual['vehicle_starts']):
        logger.error("vehicle_starts contains non-integer values")
        distance_matrix_data_actual['vehicle_starts'] = [int(idx) for idx in distance_matrix_data_actual['vehicle_starts']]
    
    if not all(isinstance(idx, int) for idx in distance_matrix_data_actual['vehicle_ends']):
        logger.error("vehicle_ends contains non-integer values")
        distance_matrix_data_actual['vehicle_ends'] = [int(idx) for idx in distance_matrix_data_actual['vehicle_ends']]
    
    try:
        manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix_data_actual["distance_matrix"]), # Use distance_matrix for node count
            len(csv_data["trucks"]),
            distance_matrix_data_actual["vehicle_starts"],
            distance_matrix_data_actual["vehicle_ends"]
        )
        routing = pywrapcp.RoutingModel(manager)
        
        vehicle_fixed_cost = 1 
        for i in range(len(csv_data["trucks"])):
            routing.SetFixedCostOfVehicle(vehicle_fixed_cost, i)
        logger.info(f"Set fixed cost of {vehicle_fixed_cost} for each of the {len(csv_data['trucks'])} vehicles.")
        
        # --- SET PRIMARY ARC COST EVALUATOR ---
        # This will now use fuel and labor costs.
        # The distance dimension (for range constraints) will use its own distance callback.
        try:
            add_total_cost_dimension_and_evaluator(routing, manager, csv_data, distance_matrix_data_actual)
            logger.info("Primary arc cost evaluator (fuel + labor) set successfully.")
        except Exception as e:
            logger.error(f"Error setting primary arc cost evaluator: {str(e)}", exc_info=True)
            raise

        # --- ADD OTHER DIMENSIONS (Distance for range, Volume, Weight) ---
        try:
            # The distance dimension for vehicle range limits still uses the pure distance callback.
            add_distance_dimension(routing, manager, csv_data, distance_matrix_data_actual)
            logger.debug("Distance dimension (for range limits) added successfully")
        except Exception as e:
            logger.error(f"Error adding distance dimension for range: {str(e)}", exc_info=True)
            raise
        
        try:
            add_volume_dimension(routing, manager, csv_data, distance_matrix_data_actual)
            logger.debug("Volume dimension added successfully")
        except Exception as e:
            logger.error(f"Error adding volume dimension: {str(e)}", exc_info=True)
            raise
        
        try:
            add_weight_dimension(routing, manager, csv_data, distance_matrix_data_actual)
            logger.debug("Weight dimension added successfully")
        except Exception as e:
            logger.error(f"Error adding weight dimension: {str(e)}", exc_info=True)
            raise
        
        logger.info("Disjunctions for dropping nodes are DISABLED for this run.")
        
        try:
            add_pickup_delivery_constraints(routing, manager, distance_matrix_data_actual,
                                          volume_dim_name="Volume",
                                          weight_dim_name="Weight")
            logger.info("Pickup delivery constraints ENABLED.")
        except Exception as e:
            logger.error(f"Error adding pickup delivery constraints: {str(e)}", exc_info=True)
            logger.warning("Continuing without pickup/delivery constraints due to error during their setup.")
        
        logger.debug("Successfully set up VRP model")
        return routing, manager
    except Exception as e:
        logger.error(f"Error in setup_vrp: {e}", exc_info=True)
        raise
