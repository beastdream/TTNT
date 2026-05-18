import heapq
import math
from collections import defaultdict


def _as_positive_float(value):
    if isinstance(value, list):
        value = value[0] if value else None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number) or number < 0:
        return None
    return number


def _edge_candidates(edge_data):
    if not edge_data:
        return []

    # MultiDiGraph: {edge_key: {length: ...}}
    if all(isinstance(data, dict) for data in edge_data.values()):
        return list(edge_data.values())

    # DiGraph: {length: ..., geometry: ...}
    return [edge_data]


def get_best_edge_data(edge_data):
    """Return the shortest edge attributes between two nodes."""
    best_data = None
    best_length = float("inf")

    for data in _edge_candidates(edge_data):
        length = _as_positive_float(data.get("length"))
        if length is not None and length < best_length:
            best_data = data
            best_length = length

    return best_data


def get_edge_length(edge_data):
    """
    Lay chieu dai canh an toan tu DiGraph hoac MultiDiGraph.

    Tra ve None neu canh khong co length hop le. Khong gan 0 mac dinh,
    vi canh 0 met co the lam sai ket qua duong ngan nhat.
    """
    best_data = get_best_edge_data(edge_data)
    if best_data is None:
        return None
    return _as_positive_float(best_data.get("length"))


def heuristic(G, a, b, mode="walk"):
    lat1, lon1 = G.nodes[a]["y"], G.nodes[a]["x"]
    lat2, lon2 = G.nodes[b]["y"], G.nodes[b]["x"]

    radius = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    value = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    value = max(0.0, min(1.0, value))
    return 2 * radius * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def _reconstruct_path(came_from, start, goal):
    current = goal
    path = [current]

    while current != start:
        current = came_from[current]
        path.append(current)

    path.reverse()
    return path


def _result(algorithm, path, distance, visited_count, max_frontier_size):
    return {
        "algorithm": algorithm,
        "path": path,
        "distance": distance,
        "visited_count": visited_count,
        "max_frontier_size": max_frontier_size,
    }


def astar_search(G, start, goal, mode="walk"):
    open_set = []
    counter = 0
    heapq.heappush(open_set, (heuristic(G, start, goal, mode), counter, 0, start))

    came_from = {}
    g_score = defaultdict(lambda: float("inf"))
    g_score[start] = 0

    visited_count = 0
    max_frontier_size = 1

    while open_set:
        _, _, current_distance, current = heapq.heappop(open_set)

        if current_distance > g_score[current]:
            continue

        visited_count += 1

        if current == goal:
            path = _reconstruct_path(came_from, start, goal)
            return _result("astar", path, g_score[goal], visited_count, max_frontier_size)

        for neighbor in G.neighbors(current):
            length = get_edge_length(G.get_edge_data(current, neighbor))
            if length is None:
                continue

            tentative_distance = current_distance + length
            if tentative_distance < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_distance
                counter += 1
                priority = tentative_distance + heuristic(G, neighbor, goal, mode)
                heapq.heappush(open_set, (priority, counter, tentative_distance, neighbor))
                max_frontier_size = max(max_frontier_size, len(open_set))

    return None


def dijkstra_search(G, start, goal, mode="walk"):
    open_set = []
    counter = 0
    heapq.heappush(open_set, (0, counter, start))

    came_from = {}
    distance = defaultdict(lambda: float("inf"))
    distance[start] = 0

    visited_count = 0
    max_frontier_size = 1

    while open_set:
        current_distance, _, current = heapq.heappop(open_set)

        if current_distance > distance[current]:
            continue

        visited_count += 1

        if current == goal:
            path = _reconstruct_path(came_from, start, goal)
            return _result("dijkstra", path, distance[goal], visited_count, max_frontier_size)

        for neighbor in G.neighbors(current):
            length = get_edge_length(G.get_edge_data(current, neighbor))
            if length is None:
                continue

            tentative_distance = current_distance + length
            if tentative_distance < distance[neighbor]:
                came_from[neighbor] = current
                distance[neighbor] = tentative_distance
                counter += 1
                heapq.heappush(open_set, (tentative_distance, counter, neighbor))
                max_frontier_size = max(max_frontier_size, len(open_set))

    return None


def shortest_path_search(G, start, goal, algorithm="astar", mode="walk"):
    if algorithm == "dijkstra":
        return dijkstra_search(G, start, goal, mode)
    return astar_search(G, start, goal, mode)


def astar(G, start, goal, mode="walk"):
    """Wrapper cu: chi tra ve danh sach node duong di."""
    result = astar_search(G, start, goal, mode)
    return result["path"] if result else None


def dijkstra(G, start, goal, mode="walk"):
    """Wrapper tuong tu astar(): chi tra ve danh sach node duong di."""
    result = dijkstra_search(G, start, goal, mode)
    return result["path"] if result else None


def path_to_coordinates(G, path):
    """Convert node path thanh danh sach [lat, lon] de Leaflet ve duong."""
    if not path:
        return []

    if len(path) == 1:
        node = G.nodes[path[0]]
        return [[node["y"], node["x"]]]

    coordinates = []

    for u, v in zip(path[:-1], path[1:]):
        edge = get_best_edge_data(G.get_edge_data(u, v))

        if edge is not None and edge.get("geometry") is not None:
            segment = [[lat, lon] for lon, lat in edge["geometry"].coords]
        else:
            u_node = G.nodes[u]
            v_node = G.nodes[v]
            segment = [[u_node["y"], u_node["x"]], [v_node["y"], v_node["x"]]]

        if coordinates and segment and coordinates[-1] == segment[0]:
            coordinates.extend(segment[1:])
        else:
            coordinates.extend(segment)

    return coordinates
