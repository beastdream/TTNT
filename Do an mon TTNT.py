from flask import Flask, render_template, request, jsonify
import requests

# Các import cũ phục vụ thuật toán cục bộ A* (Đã được comment lại để tăng tốc khởi động)
# import osmnx as ox
# from Astar import astar

app = Flask(__name__)

# ==========================================
# CẤU HÌNH API
# ==========================================
# Điền Google Maps API Key vào đây (Ví dụ: "AIzaSy...")
# Nếu rỗng, ứng dụng sẽ tự động dùng OSRM API miễn phí thay thế.
GOOGLE_MAPS_API_KEY = "" 

# Code cũ tải bản đồ cục bộ:
# print("Đang tải bản đồ...")
# G = ox.graph_from_place("Thu Duc, Vietnam", network_type="all")
# print("Tải xong bản đồ")

def decode_polyline(polyline_str):
    """Giải mã polyline của Google Maps thành danh sách tọa độ [lat, lon]"""
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    while index < len(polyline_str):
        for unit in ['latitude', 'longitude']: 
            shift, result = 0, 0
            while True:
                if index >= len(polyline_str):
                    break
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break
            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']
        coordinates.append([lat / 100000.0, lng / 100000.0])

    return coordinates

def get_google_route(start_lat, start_lon, end_lat, end_lon, mode):
    # Google Maps tự nhận "driving" và "walking"
    gmaps_mode = "driving" if mode == "drive" else "walking"
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{start_lat},{start_lon}",
        "destination": f"{end_lat},{end_lon}",
        "mode": gmaps_mode,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "OK":
            route = data["routes"][0]
            leg = route["legs"][0]
            
            distance = leg["distance"]["value"] # mét
            time = leg["duration"]["value"] / 60.0 # phút
            
            polyline_str = route["overview_polyline"]["points"]
            coords = decode_polyline(polyline_str)
            
            return {
                "coords": coords,
                "distance": distance,
                "time": time,
                "provider": "google"
            }
        else:
            print("Lỗi từ Google Maps API:", data.get("status"), data.get("error_message"))
            return None
    except Exception as e:
        print("Lỗi kết nối tới Google Maps API:", e)
        return None

def get_osrm_route(start_lat, start_lon, end_lat, end_lon, mode):
    # OSRM profiles: "driving" (xe hơi) hoặc "foot" (đi bộ)
    osrm_profile = "driving" if mode == "drive" else "foot"
    # Định dạng tọa độ cho OSRM là lon,lat
    url = f"http://router.project-osrm.org/route/v1/{osrm_profile}/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("code") == "Ok":
            route = data["routes"][0]
            
            distance = route["distance"] # mét
            time = route["duration"] / 60.0 # phút
            
            # Giải mã GeoJSON: danh sách các điểm [lon, lat] => cần chuyển thành [lat, lon] cho Frontend (Leaflet)
            coords = [[coord[1], coord[0]] for coord in route["geometry"]["coordinates"]]
            
            return {
                "coords": coords,
                "distance": distance,
                "time": time,
                "provider": "osrm"
            }
        else:
            print("Lỗi từ OSRM API:", data.get("code"))
            return None
    except Exception as e:
        print("Lỗi kết nối tới OSRM API:", e)
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/route", methods=["POST"])
def route():
    data = request.json
    mode = data.get("mode", "walk")

    start_lat = data["start_lat"]
    start_lon = data["start_lon"]
    end_lat = data["end_lat"]
    end_lon = data["end_lon"]

    result = None

    # 1. Ưu tiên sử dụng Google API nếu có nhập API Key
    if GOOGLE_MAPS_API_KEY.strip() != "":
        print("Đang tìm đường bằng Google Maps API...")
        result = get_google_route(start_lat, start_lon, end_lat, end_lon, mode)
    
    # 2. Xài OSRM API làm phương án miễn phí (Fallback)
    if result is None:
        if GOOGLE_MAPS_API_KEY.strip() == "":
            print("Chưa có API Key, đang dùng OSRM API (miễn phí) để thay thế...")
        else:
            print("Google API bị lỗi, tự động chuyển về OSRM API...")
        result = get_osrm_route(start_lat, start_lon, end_lat, end_lon, mode)

    # 3. Code dự phòng khi mất kết nối mạng
    if result is None:
        return jsonify({
            "coords": [],
            "distance": 0,
            "time": 0,
            "error": "Không thể kết nối với dịch vụ tìm đường."
        })

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)

