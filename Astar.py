import heapq
import math

def heuristic(G, a, b, mode="walk"):
    # Lấy tọa độ Lat/Lon
    lat1, lon1 = G.nodes[a]['y'], G.nodes[a]['x']
    lat2, lon2 = G.nodes[b]['y'], G.nodes[b]['x']
    
    # Công thức Haversine để tính khoảng cách (mét) chính xác trên trái đất
    R = 6371000  # Bán kính trái đất tính bằng mét
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a_hav = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    dist = 2 * R * math.atan2(math.sqrt(a_hav), math.sqrt(1 - a_hav))
    
    if mode == "drive":
        # Tối ưu cho lái xe: Ước lượng thời gian (giây) với vận tốc 80km/h (22.2 m/s)
        # Chia cho vận tốc cao nhất để đảm bảo heuristic luôn hợp lệ (admissible)
        return dist / 22.2
    else:
        # Tối ưu cho đi bộ: Khoảng cách mét chia cho tốc độ đi bộ nhanh (1.5 m/s)
        return dist / 1.5

def astar(G, start, goal, mode="walk"):
    open_set = []
    # Lưu thêm mode vào hàm để heuristic sử dụng
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {node: float('inf') for node in G.nodes}
    g_score[start] = 0

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]

        for neighbor in G.neighbors(current):
            edge_data = G.get_edge_data(current, neighbor)
            if edge_data is None: continue
            
            # Lấy chiều dài cạnh (length)
            if isinstance(edge_data, dict):
                length = edge_data[0].get('length', 0) if 0 in edge_data else list(edge_data.values())[0].get('length', 0)
            else:
                length = edge_data.get('length', 0)

            # Nếu là drive, chi phí thực tế nên là length / speed_limit, 
            # nhưng ở mức đơn giản ta dùng length.
            tentative = g_score[current] + length

            if tentative < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                # Truyền mode vào đây
                f = tentative + heuristic(G, neighbor, goal, mode)
                heapq.heappush(open_set, (f, neighbor))
    return None