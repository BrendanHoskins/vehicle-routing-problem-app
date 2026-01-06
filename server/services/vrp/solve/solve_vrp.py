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
        (routing_enums_pb2.FirstSolutionStrategy.CHRISTOFIDES, "CHRISTOFIDES"),
        (routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC, "AUTOMATIC")
    ]
    
    for strategy_enum, strategy_name in strategies:
        try:
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = strategy_enum
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.FromSeconds(30)  # Reduced time limit for faster feedback during debugging
            search_parameters.log_search = True
            
            logger.debug(f"Trying strategy: {strategy_name}")
            solution = routing.SolveWithParameters(search_parameters)
            
            if solution:
                logger.debug(f"Found solution with strategy: {strategy_name}")
                
                # --- START: DEBUG: Check for dropped nodes if disjunctions were used ---
                # The previous attempt to use routing.DisjunctionNode in the solution was incorrect.
                # The most reliable ways to check for dropped nodes are:
                # 1. Observe if the solution.ObjectiveValue() is very high (suggesting penalties were paid).
                # 2. In your format_solution function, iterate through all nodes that *should* have been
                #    visited (those with disjunctions) and see if they appear in any vehicle's route.
                
                logger.info(f"Solution Objective Value: {solution.ObjectiveValue()}")
                # Assuming a penalty of 1,000,000 was used in setup_vrp.py for dropping a node.
                # If the objective value is around this magnitude or higher (plus actual travel costs),
                # it's a strong indicator nodes were dropped.
                # Example: If penalty is 1,000,000 and 3 nodes were dropped, objective might be > 3,000,000.
                if routing.GetNumberOfDisjunctions() > 0 and solution.ObjectiveValue() >= 1000000 : 
                    logger.warning("High objective value suggests some mandatory nodes may have been dropped. "
                                   "Please inspect the routes in format_solution to identify unvisited mandatory nodes.")
                # --- END: DEBUG ---

                return solution, routing, manager
            else:
                logger.debug(f"No solution found with strategy: {strategy_name}")
        except RuntimeError as e: # Catching RuntimeError which OR-Tools sometimes throws for invalid params
            logger.error(f"RuntimeError with strategy {strategy_name}: {str(e)}. This might indicate an issue with strategy compatibility (e.g., SWEEP).")
        except Exception as e:
            logger.error(f"Error with strategy {strategy_name}: {str(e)}")
    
    # If no solution is found after trying all strategies
    logger.error("No solution found with any strategy")
    return None, routing, manager
