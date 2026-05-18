import os
import threading
import time

from flask import Flask, jsonify, render_template, request

from algorithm import path_to_coordinates, shortest_path_search


app = Flask(__name__)

# ==========================================
# CẤU HÌNH
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")

# Bounding box Thủ Đức: (left, bottom, right, top) = (lon_min, lat_min, lon_max, lat_max)
THU_DUC_BBOX = (106.70, 10.80, 106.85, 10.90)

LOCAL_ALGORITHMS = {"astar", "dijkstra"}
GRAPH_CACHE = {}
GRAPH_LOCK = threading.Lock()


def safe_print(*parts):
    message = " ".join(str(part) for part in parts)
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("ascii", errors="backslashreplace").decode("ascii"))


def get_osmnx():
    import osmnx as ox

    ox.settings.use_cache = True
    ox.settings.cache_folder = CACHE_DIR
    ox.settings.log_console = False
    return ox


def graph_network_type(mode):
    return "drive" if mode == "drive" else "walk"


def get_graph(mode):
    network_type = graph_network_type(mode)

    with GRAPH_LOCK:
        if network_type in GRAPH_CACHE:
            return GRAPH_CACHE[network_type]

        ox = get_osmnx()
        safe_print(f"Đang tải graph OSMnx ({network_type}) cho khu vực Thủ Đức...")
        started_at = time.perf_counter()

        graph = ox.graph_from_bbox(
            THU_DUC_BBOX,
            network_type=network_type,
            simplify=True,
            retain_all=False,
        )

        elapsed = time.perf_counter() - started_at
        GRAPH_CACHE[network_type] = graph
        safe_print(
            f"Tải xong graph {network_type}: "
            f"{len(graph.nodes):,} nodes, {len(graph.edges):,} edges trong {elapsed:.2f}s"
        )
        return graph


def estimate_time_minutes(distance_meters, mode):
    # Tốc độ ước lượng đủ dùng cho demo thuật toán:
    # đi bộ 4.8 km/h tương đương 80 m/phút
    # ô tô 30 km/h tương đương 500 m/phút
    speed_m_per_minute = 500 if mode == "drive" else 80
    return distance_meters / speed_m_per_minute if speed_m_per_minute else 0


def get_local_route(start_lat, start_lon, end_lat, end_lon, mode, algorithm):
    ox = get_osmnx()
    graph = get_graph(mode)

    # Vì thuật toán chỉ chạy trên node của graph,
    # điểm người dùng click sẽ được ánh xạ về node gần nhất.
    start_node, start_snap = ox.distance.nearest_nodes(
        graph,
        X=start_lon,
        Y=start_lat,
        return_dist=True,
    )

    end_node, end_snap = ox.distance.nearest_nodes(
        graph,
        X=end_lon,
        Y=end_lat,
        return_dist=True,
    )

    started_at = time.perf_counter()
    search_result = shortest_path_search(graph, start_node, end_node, algorithm, mode)
    elapsed = time.perf_counter() - started_at

    if search_result is None:
        return None

    coords = path_to_coordinates(graph, search_result["path"])
    distance = float(search_result["distance"])

    # Tọa độ node thực tế mà thuật toán dùng để bắt đầu/kết thúc.
    # Các tọa độ này sẽ được gửi về frontend để vẽ đường nét đứt
    # từ marker người dùng chọn đến node gần nhất trên graph.
    start_node_data = graph.nodes[start_node]
    end_node_data = graph.nodes[end_node]

    snapped_start = [start_node_data["y"], start_node_data["x"]]
    snapped_end = [end_node_data["y"], end_node_data["x"]]

    return {
        "coords": coords,
        "distance": distance,
        "time": estimate_time_minutes(distance, mode),
        "provider": "local-osmnx",
        "algorithm": search_result["algorithm"],
        "visited_count": int(search_result["visited_count"]),
        "max_frontier_size": int(search_result["max_frontier_size"]),
        "path_nodes": len(search_result["path"]),
        "runtime_ms": round(elapsed * 1000, 2),

        # Node bắt đầu/kết thúc sau khi bám vào graph
        "start_node": int(start_node),
        "end_node": int(end_node),

        # Tổng sai số bám đường
        "snap_distance": round(float(start_snap + end_snap), 2),

        # Sai số riêng từng điểm
        "start_snap_distance": round(float(start_snap), 2),
        "end_snap_distance": round(float(end_snap), 2),

        # Tọa độ node gần nhất trên graph
        "snapped_start": snapped_start,
        "snapped_end": snapped_end,
    }


def get_number(payload, key):
    value = payload.get(key)
    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, f"Thiếu hoặc sai định dạng trường '{key}'."


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/route", methods=["POST"])
def route():
    data = request.get_json(silent=True) or {}

    start_lat, error = get_number(data, "start_lat")
    if error:
        return jsonify({"error": error}), 400

    start_lon, error = get_number(data, "start_lon")
    if error:
        return jsonify({"error": error}), 400

    end_lat, error = get_number(data, "end_lat")
    if error:
        return jsonify({"error": error}), 400

    end_lon, error = get_number(data, "end_lon")
    if error:
        return jsonify({"error": error}), 400

    mode = data.get("mode", "walk")
    if mode not in {"walk", "drive"}:
        mode = "walk"

    algorithm = data.get("algorithm", "astar")
    if algorithm not in LOCAL_ALGORITHMS:
        algorithm = "astar"

    try:
        result = get_local_route(start_lat, start_lon, end_lat, end_lon, mode, algorithm)
    except Exception as exc:
        safe_print("Lỗi thuật toán cục bộ:", exc)
        return jsonify(
            {
                "coords": [],
                "distance": 0,
                "time": 0,
                "error": f"Lỗi khi chạy {algorithm.upper()} trên graph cục bộ.",
            }
        ), 500

    if result is None:
        return jsonify(
            {
                "coords": [],
                "distance": 0,
                "time": 0,
                "error": "Thuật toán cục bộ không tìm thấy đường đi giữa hai điểm.",
            }
        ), 404

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))