import heapq
import math
from collections import defaultdict

def get_edge_length(edge_data):
    """
    Hàm lấy chiều dài (length) an toàn từ dữ liệu cạnh của đồ thị.
    Giải quyết lỗi AttributeError khi edge_data là DiGraph attributes thay vì MultiDiGraph dicts.
    """
    if not edge_data:
        return 0
    min_length = float('inf')
    
    # Trường hợp MultiDiGraph: edge_data chứa các dictionary con
    for key, data in edge_data.items():
        if isinstance(data, dict) and 'length' in data:
            l = data['length']
            if isinstance(l, list): l = l[0] # OSmnx có thể trả về list
            try:
                min_length = min(min_length, float(l))
            except (ValueError, TypeError):
                pass
                
    if min_length != float('inf'):
        return min_length
        
    # Trường hợp DiGraph: edge_data là thông tin cạnh trực tiếp
    if 'length' in edge_data:
        l = edge_data['length']
        if isinstance(l, list): l = l[0]
        try:
            return float(l)
        except (ValueError, TypeError):
            return 0
            
    return 0

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
    # Đảm bảo a_hav nằm trong khoảng [0, 1] tránh lỗi domain do sai số float
    a_hav = max(0.0, min(1.0, a_hav))
    dist = 2 * R * math.atan2(math.sqrt(a_hav), math.sqrt(1 - a_hav))
    
    # TRỌNG TÂM SỬA LỖI:
    # f = g + h. Vì g_score được tính bằng tổng chiều dài (mét), h cũng phải tính bằng mét.
    # Việc chia cho tốc độ (22.2 hay 1.5) sẽ dẫn đến sai đơn vị (mét + giây)
    # khiến hàm A* bị mất định hướng không gian, quét cực kỳ chậm và dễ bị hết Ram/treo máy.
    return dist

def astar(G, start, goal, mode="walk"):
    open_set = []
    count = 0 # Count đóng vai trò tie-breaker an toàn khi f bằng nhau
    heapq.heappush(open_set, (0, count, 0, start))
    came_from = {}
    
    # Tránh khởi tạo dict kích thước bằng số lượng node của bản đồ (tối ưu RAM / thời gian)
    g_score = defaultdict(lambda: float('inf'))
    g_score[start] = 0

    while open_set:
        f_current, _, g_current, current = heapq.heappop(open_set)
        
        # Bỏ qua nếu có đường đi khác tốt hơn đến node này rồi (tránh xét lại Node cũ với chi phí tệ hơn)
        if g_current > g_score[current]:
            continue

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
            
            # Lấy chiều dài an toàn (tránh văng lỗi AttributeError)
            length = get_edge_length(edge_data)

            # Do tính toán đơn giản nên ta dùng length (mét) làm g_cost
            tentative = g_score[current] + length

            if tentative < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                f = tentative + heuristic(G, neighbor, goal, mode)
                count += 1
                heapq.heappush(open_set, (f, count, tentative, neighbor))
    return None