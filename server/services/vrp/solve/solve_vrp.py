from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import logging
import sys

# Setup logging
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def solve_vrp(routing, manager):
    # Add debugging before solving
    logger.debug(f"Starting solve_vrp with {manager.GetNumberOfNodes()} nodes and {manager.GetNumberOfVehicles()} vehicles")
    
    # Try various strategies if one fails
    strategies = [
        (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC, "PATH_CHEAPEST_ARC"),
        (routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION, "PARALLEL_CHEAPEST_INSERTION"),
        (routing_enums_pb2.FirstSolutionStrategy.SAVINGS, "SAVINGS"),
        (routing_enums_pb2.FirstSolutionStrategy.SWEEP, "SWEEP"),
        (routing_enums_pb2.FirstSolutionStrategy.CHRISTOFIDES, "CHRISTOFIDES")
    ]
    
    for strategy_enum, strategy_name in strategies:
        try:
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = strategy_enum
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.FromSeconds(60)  # Increased time limit
            search_parameters.log_search = True
            
            logger.debug(f"Trying strategy: {strategy_name}")
            solution = routing.SolveWithParameters(search_parameters)
            
            if solution:
                logger.debug(f"Found solution with strategy: {strategy_name}")
                return solution, routing, manager
            else:
                logger.debug(f"No solution found with strategy: {strategy_name}")
        except Exception as e:
            logger.error(f"Error with strategy {strategy_name}: {str(e)}")
    
    # If no solution is found after trying all strategies
    logger.error("No solution found with any strategy")
    return None, routing, manager
