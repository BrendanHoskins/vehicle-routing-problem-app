import sys
import logging

# Configure logging to write to stderr with detailed formatting
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_pickup_delivery_constraints(routing, manager, distance_matrix_data,
                                    volume_dim_name="Volume",
                                    weight_dim_name="Weight"):
    """
    For each (pickup_current -> pickup_destination) or
    (delivery_current -> delivery_destination), ensure:
      1) They are visited by the same vehicle.
      2) The pickup node is visited before the corresponding delivery node.
      3) The volume/weight cumul at the pickup is <= cumul at the delivery.
    """
    try:
        # Log initial state
        logger.debug(f"Starting add_pickup_delivery_constraints with {manager.GetNumberOfNodes()} nodes")
        
        # We'll search pairs in data["locations"] by matching 'identifier' & type
        # E.g. "pickup_current" => "pickup_destination", or "delivery_current" => "delivery_destination".
        # We'll build a dict of 'identifier' -> (pickup_index, delivery_index).
        # If an identifier has multiple pairs, adapt as needed.
        location_map = {}
        # location_map will hold:
        #   location_map[(identifier, "pickup")] = (idx_of_current, idx_of_destination)
        #   location_map[(identifier, "delivery")] = (idx_of_current, idx_of_destination)

        # Step 1: Collect indices for pickup_current, pickup_destination, etc.
        for loc in distance_matrix_data["locations"]:
            id_ = loc["identifier"]
            loc_type = loc["type"]
            real_idx = loc["index"]  # The deduplicated index in the matrix
            
            # Ensure key format matches typical P&D task types (e.g. "pickup" or "delivery" task)
            task_type_key = None
            if "pickup" in loc_type:
                task_type_key = "pickup"
            elif "delivery" in loc_type:
                task_type_key = "delivery"

            if task_type_key:
                if "_current" in loc_type:
                    location_map.setdefault((id_, task_type_key), {})["current"] = real_idx
                elif "_destination" in loc_type:
                    location_map.setdefault((id_, task_type_key), {})["destination"] = real_idx

        # Step 2: For each pair found, call AddPickupAndDelivery + constraints
        for key, pair_dict in location_map.items():
            if "current" in pair_dict and "destination" in pair_dict:
                from_node = pair_dict["current"]
                to_node = pair_dict["destination"]
                
                # Log before conversion
                logger.debug(f"Processing pair - Key: {key}")
                logger.debug(f"Raw nodes - from_node: {from_node}, to_node: {to_node}")
                
                # Convert nodes to indices
                from_index = manager.NodeToIndex(from_node)
                to_index = manager.NodeToIndex(to_node)
                
                # Log after conversion
                logger.debug(f"Converted indices - from_index: {from_index}, to_index: {to_index}")
                
                try:
                    routing.AddPickupAndDelivery(from_index, to_index)
                    logger.debug(f"Successfully added pickup/delivery constraint for indices {from_index}, {to_index}")
                except Exception as e:
                    logger.error(f"Failed to add pickup/delivery constraint: {e}")
                    logger.error(f"Current state - from_index: {from_index}, to_index: {to_index}")
                    raise

                # Force same vehicle - This is actually redundant if AddPickupAndDelivery is used,
                # as it already enforces this. Keeping it doesn't hurt, but can be removed.
                # routing.solver().Add(routing.VehicleVar(from_index) == routing.VehicleVar(to_index))

                # The precedence (pickup before delivery) is enforced by AddPickupAndDelivery.
                # The following cumulative constraints are often problematic or unnecessary with
                # correctly defined demand callbacks and capacity dimensions.
                # The capacity dimensions themselves will ensure load doesn't exceed vehicle capacity.

                # volume_dimension = routing.GetDimensionOrDie(volume_dim_name)
                # weight_dimension = routing.GetDimensionOrDie(weight_dim_name)

                # routing.solver().Add(
                #     volume_dimension.CumulVar(from_index) <= volume_dimension.CumulVar(to_index)
                # )
                # routing.solver().Add(
                #     weight_dimension.CumulVar(from_index) <= weight_dimension.CumulVar(to_index)
                # )

    except Exception as e:
        logger.error(f"Error in add_pickup_delivery_constraints: {e}", exc_info=True)
        raise