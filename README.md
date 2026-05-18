# Đồ án Nhập môn Trí tuệ nhân tạo

## Tìm đường ngắn nhất bằng A\* và Dijkstra trên bản đồ Thủ Đức

## 1. Giới thiệu

Đây là đồ án nhỏ cho môn **Nhập môn Trí tuệ nhân tạo**, xây dựng ứng dụng tìm đường ngắn nhất giữa hai điểm trong khu vực **Thủ Đức**.

Ứng dụng sử dụng dữ liệu bản đồ từ **OpenStreetMap** thông qua thư viện **OSMnx**, sau đó biểu diễn mạng lưới đường đi dưới dạng đồ thị. Trên đồ thị này, chương trình tự cài đặt và so sánh hai thuật toán tìm đường:

- **Dijkstra**
- **A\***

Mục tiêu của đồ án là minh họa bài toán tìm kiếm đường đi trong trí tuệ nhân tạo, đồng thời so sánh hiệu quả giữa thuật toán tìm kiếm không heuristic và thuật toán tìm kiếm có heuristic.

---

## 2. Chức năng chính

Ứng dụng hỗ trợ các chức năng sau:

- Hiển thị bản đồ khu vực Thủ Đức bằng Leaflet.
- Cho phép người dùng chọn điểm bắt đầu và điểm kết thúc trực tiếp trên bản đồ.
- Hỗ trợ tìm đường theo hai chế độ:
  - Đi bộ
  - Ô tô
- Cho phép chọn thuật toán:
  - A\*
  - Dijkstra
- Vẽ đường đi tìm được lên bản đồ.
- Hiển thị các thông tin kết quả:
  - Thuật toán sử dụng
  - Khoảng cách đường đi
  - Thời gian di chuyển ước lượng
  - Số node đã duyệt
  - Số node trên đường đi
  - Kích thước frontier lớn nhất
  - Thời gian chạy thuật toán
  - Sai số bám đường từ điểm chọn đến node gần nhất

---

## 3. Công nghệ sử dụng

- **Python**
- **Flask**: xây dựng backend và API xử lý tìm đường
- **OSMnx**: tải và xử lý dữ liệu bản đồ OpenStreetMap
- **Leaflet**: hiển thị bản đồ trên giao diện web
- **HTML, CSS, JavaScript**: xây dựng giao diện người dùng

---

## 4. Cấu trúc dự án

```text
.
├── app.py
├── algorithm.py
├── requirements.txt
├── README.md
├── templates
│   └── index.html
└── static
    └── script.js

Trong đó:

app.py: file chính chạy ứng dụng Flask, xử lý request từ giao diện và gọi thuật toán tìm đường.
algorithm.py: cài đặt thuật toán A*, Dijkstra và các hàm xử lý đường đi.
templates/index.html: giao diện chính của ứng dụng.
static/script.js: xử lý tương tác bản đồ, chọn điểm, gọi API và vẽ kết quả.
requirements.txt: danh sách thư viện cần cài đặt.

---
## 5. Ý nghĩa thuật toán
Dijkstra

Dijkstra là thuật toán tìm đường đi ngắn nhất từ một đỉnh bắt đầu đến các đỉnh khác trong đồ thị có trọng số không âm.

Trong đồ án này, Dijkstra luôn mở rộng node có tổng chi phí từ điểm bắt đầu nhỏ nhất. Thuật toán đảm bảo tìm được đường đi ngắn nhất, tuy nhiên có thể duyệt nhiều node vì không có thông tin định hướng về phía đích.

A*

A* là thuật toán tìm kiếm có sử dụng heuristic. Thuật toán đánh giá mỗi node bằng công thức:

f(n) = g(n) + h(n)

Trong đó:

g(n) là chi phí thực tế từ điểm bắt đầu đến node hiện tại.
h(n) là chi phí ước lượng từ node hiện tại đến đích.
f(n) là tổng chi phí dự đoán của đường đi qua node đó.

Trong đồ án này, hàm heuristic h(n) sử dụng khoảng cách Haversine giữa hai tọa độ địa lý. Nhờ heuristic này, A* thường duyệt ít node hơn Dijkstra nhưng vẫn tìm được đường đi ngắn nhất nếu heuristic không vượt quá chi phí thực tế.

---
## 6. Cách cài đặt và chạy chương trình

Bước 1: Tạo môi trường ảo
python -m venv .venv
Bước 2: Kích hoạt môi trường ảo

Trên Windows:

.venv\Scripts\activate

Trên macOS/Linux:

source .venv/bin/activate
Bước 3: Cài đặt thư viện
pip install -r requirements.txt
Bước 4: Chạy ứng dụng
python app.py

Sau đó mở trình duyệt và truy cập:

http://127.0.0.1:5000

---
## 7. Cách sử dụng


Mở ứng dụng trên trình duyệt.
Chọn chế độ di chuyển: Đi bộ hoặc Ô tô.
Chọn thuật toán: A* hoặc Dijkstra.
Nhấn lên bản đồ để chọn điểm bắt đầu.
Nhấn tiếp lên bản đồ để chọn điểm kết thúc.
Ứng dụng sẽ tìm đường và hiển thị kết quả trên bản đồ.
Có thể kéo thả điểm bắt đầu hoặc điểm kết thúc để chạy lại thuật toán.
Nhấn Reset để chọn lại từ đầu.

---
## 8. Ghi chú

Lần đầu chạy chương trình có thể mất thời gian vì OSMnx cần tải dữ liệu bản đồ khu vực Thủ Đức.
Những lần chạy sau sẽ nhanh hơn nhờ dữ liệu được lưu trong thư mục cache.
Ứng dụng không sử dụng API tìm đường bên ngoài; đường đi được tính bằng thuật toán cài đặt trong chương trình.
Chức năng tìm kiếm địa điểm chỉ hỗ trợ người dùng xác định vị trí trên bản đồ, không dùng để tính đường đi.


---
## 9. Kết luận

Đồ án đã xây dựng được một ứng dụng trực quan để minh họa bài toán tìm đường ngắn nhất trong trí tuệ nhân tạo.

Thông qua việc so sánh A* và Dijkstra, đồ án cho thấy vai trò của heuristic trong việc giảm số lượng node cần duyệt, từ đó giúp thuật toán tìm kiếm hoạt động hiệu quả hơn trong nhiều trường hợp thực tế.
```
