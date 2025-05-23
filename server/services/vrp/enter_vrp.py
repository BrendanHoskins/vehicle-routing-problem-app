from server.services.csv.handle_excel_file import ExcelFileProcessor
from server.services.google_routes_api.get_route_matrix import create_distance_matrix
from server.services.vrp.solve.setup_vrp import setup_vrp
from server.services.vrp.solve.solve_vrp import solve_vrp
from server.services.vrp.solve.format_vrp_solution import format_solution

def enter_vrp_flow(files_data):
    processed_csv_data = ExcelFileProcessor().process_file(files_data)

    distance_matrix_data = create_distance_matrix(processed_csv_data['deliveries'], processed_csv_data['depots'], processed_csv_data['trucks'], processed_csv_data['pickups'])

    routing, manager = setup_vrp(processed_csv_data, distance_matrix_data["data"])

    raw_solution, routing, manager = solve_vrp(routing, manager)

    final_solution = format_solution(processed_csv_data, distance_matrix_data["data"], manager, routing, raw_solution)

    return final_solution



    