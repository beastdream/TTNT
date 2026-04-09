from flask import Flask, render_template, request, jsonify
import osmnx as ox
from Astar import astar

app = Flask(__name__)

print("Đang tải bản đồ...")
G = ox.graph_from_place("Thu Duc, Vietnam", network_type="all")
#G = ox.project_graph(G)
print("Tải xong bản đồ")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/route", methods=["POST"])
def route():
    data = request.json
    # =========================
    # LẤY MODE (THÊM Ở ĐÂY)
    # =========================
    mode = data.get("mode", "walk")

    if mode == "drive":
        speed = 40   # km/h
    else:
        speed = 5    # km/h
    start_lat = data["start_lat"]
    start_lon = data["start_lon"]
    end_lat = data["end_lat"]
    end_lon = data["end_lon"]

    start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)

    path = astar(G, start_node, end_node, mode)

    if path is None:
        return jsonify({
            "coords": [],
            "distance": 0,
            "time": 0
        })

    # Lấy tọa độ
    # =========================
    # LẤY TỌA ĐỘ CHI TIẾT (ĐÃ SỬA ĐỂ BÁM SÁT MẶT ĐƯỜNG)
    # =========================
    coords = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        edge_data = G.get_edge_data(u, v)
        
        if edge_data is None:
            continue

        # Lấy dữ liệu cạnh đầu tiên (OSMnx MultiDiGraph)
        if isinstance(edge_data, dict):
            # Thường là key 0, nếu không có thì lấy cạnh đầu tiên
            data = edge_data[0] if 0 in edge_data else list(edge_data.values())[0]
        else:
            data = edge_data

        # KIỂM TRA GEOMETRY: Nếu có đường cong thì lấy toàn bộ các điểm trung gian
        if 'geometry' in data:
            # geometry.coords là danh sách các điểm (longitude, latitude)
            for point in data['geometry'].coords:
                coords.append([point[1], point[0]]) # Đảo lại thành [lat, lon] cho Leaflet
        else:
            # Nếu là đường thẳng (không có geometry), chỉ cần lấy tọa độ node đầu
            coords.append([G.nodes[u]['y'], G.nodes[u]['x']])

    # Thêm tọa độ của node cuối cùng vào danh sách
    coords.append([G.nodes[path[-1]]['y'], G.nodes[path[-1]]['x']])

    # =========================
    # TÍNH KHOẢNG CÁCH (THÊM Ở ĐÂY)
    # =========================
    # =========================
    # TÍNH KHOẢNG CÁCH (ĐÃ SỬA)
    # =========================
    # total_length = 0

    # for i in range(len(path) - 1):
    #     u, v = path[i], path[i+1]
    #     edge_data = G.get_edge_data(u, v)

    #     if edge_data is None:
    #         continue  # Bỏ qua nếu không tìm thấy dữ liệu cạnh

    #     if isinstance(edge_data, dict):
    #         # Kiểm tra key 0 (mặc định của OSMnx MultiDiGraph)
    #         if 0 in edge_data:
    #             total_length += edge_data[0].get('length', 0)
    #         else:
    #             # Nếu không có key 0, lấy giá trị của cạnh đầu tiên tìm thấy
    #             total_length += list(edge_data.values())[0].get('length', 0)
    #     else:
    #         total_length += edge_data.get('length', 0)

    total_length = 0
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        edge_data = G.get_edge_data(u, v)
        if edge_data is None: continue
        
        # Logic an toàn để lấy length từ MultiDiGraph
        if isinstance(edge_data, dict):
            if 0 in edge_data:
                length = edge_data[0].get('length', 0)
            else:
                length = list(edge_data.values())[0].get('length', 0)
        else:
            length = edge_data.get('length', 0)
            
        total_length += length

    # =========================
    # TÍNH THỜI GIAN (THÊM Ở ĐÂY)
    # =========================
    time = total_length / 1000 / speed * 60  # phút

    # =========================
    # TRẢ KẾT QUẢ
    # =========================
    return jsonify({
        "coords": coords,
        "distance": total_length,
        "time": time
    })

if __name__ == "__main__":
    app.run(debug=True)
