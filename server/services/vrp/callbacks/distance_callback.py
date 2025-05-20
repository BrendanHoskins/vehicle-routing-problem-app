def distance_callback(from_index, to_index, manager, distance_matrix_data):
    """Return the distance between two nodes from the matrix."""
    origin = manager.IndexToNode(from_index)
    destination = manager.IndexToNode(to_index)
    return int(distance_matrix_data["distance_matrix"][origin][destination])