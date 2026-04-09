

// Tọa độ trung tâm Thủ Đức
var thuDucCenter = [10.85, 106.77];

// Giới hạn khu vực (bounding box Thủ Đức)
var bounds = [
    [10.80, 106.70], // góc dưới trái
    [10.90, 106.85]  // góc trên phải
];

// Khởi tạo map + giới hạn vùng
var map = L.map('map', {
    center: thuDucCenter,
    zoom: 13,
    maxBounds: bounds,        // không cho kéo ra ngoài
    maxBoundsViscosity: 1.0   // kéo sẽ bị "dính" lại
});

// Thêm nền bản đồ
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    noWrap: true   // không lặp bản đồ
}).addTo(map);

// Marker test
L.marker(thuDucCenter).addTo(map)
    .bindPopup("Trung tâm Thủ Đức")
    .openPopup();

function searchLocation() {
    let query = document.getElementById("searchBox").value;

    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${query}`)
        .then(res => res.json())
        .then(data => {
            if (data.length > 0) {
                let lat = parseFloat(data[0].lat);
                let lon = parseFloat(data[0].lon);

                map.setView([lat, lon], 15);

                L.marker([lat, lon]).addTo(map)
                    .bindPopup("Kết quả tìm kiếm")
                    .openPopup();
            }
        });
}


// =========================
// CHỌN ĐIỂM + TÌM ĐƯỜNG
// =========================
let startMarker = null;
let endMarker = null;
let routeLine = null;

map.on("click", function (e) {
    let lat = e.latlng.lat;
    let lon = e.latlng.lng;

    console.log("Click:", lat, lon); // debug

    // Click lần 1 → điểm bắt đầu
    if (!startMarker) {
        startMarker = L.marker([lat, lon]).addTo(map)
            .bindPopup("Điểm bắt đầu")
            .openPopup();

        console.log("Đã chọn điểm bắt đầu");
    }

    // Click lần 2 → điểm kết thúc
    else if (!endMarker) {
        endMarker = L.marker([lat, lon]).addTo(map)
            .bindPopup("Điểm kết thúc")
            .openPopup();

        console.log("Đã chọn điểm kết thúc");

        // 👉 Gọi A*
        findRoute();
    }

    // Click lần 3 → reset
    else {
        console.log("Reset");

        map.removeLayer(startMarker);
        map.removeLayer(endMarker);
        if (routeLine) map.removeLayer(routeLine);

        startMarker = L.marker([lat, lon]).addTo(map)
            .bindPopup("Điểm bắt đầu")
            .openPopup();

        endMarker = null;
        routeLine = null;
    }
});


function findRoute() {
    fetch("/route", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            start_lat: startMarker.getLatLng().lat,
            start_lon: startMarker.getLatLng().lng,
            end_lat: endMarker.getLatLng().lat,
            end_lon: endMarker.getLatLng().lng,
            mode: document.getElementById("mode").value  // ✅ THÊM Ở ĐÂY
        })
    })
    .then(res => res.json())
    .then(data => {
        console.log("DATA:", data); 
        
        drawRoute(data.coords);

        alert("Khoảng cách: " + (data.distance / 1000).toFixed(2) + " km");
    })
    .catch(err => {
        console.error(err);
    });
}


function drawRoute(coords) {
    console.log("Vẽ route:", coords);

    if (!coords || coords.length === 0) {
        alert("Không có đường để vẽ!");
        return;
    }

    // Xóa đường cũ
    if (routeLine) {
        map.removeLayer(routeLine);
    }

    // Vẽ đường mới
    routeLine = L.polyline(coords, {
        color: "red",
        weight: 5
    }).addTo(map);

    // Zoom vào đường
    map.fitBounds(routeLine.getBounds());
}