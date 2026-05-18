var thuDucCenter = [10.85, 106.77];
var bounds = [
  [10.8, 106.7],
  [10.9, 106.85],
];

var map = L.map("map", {
  center: thuDucCenter,
  zoom: 13,
  maxBounds: bounds,
  maxBoundsViscosity: 1.0,
});

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
  noWrap: true,
}).addTo(map);

var startMarker = null;
var endMarker = null;
var searchMarker = null;
var routeLine = null;
var snapStartLine = null;
var snapEndLine = null;
var isRouting = false;

var statusEl = document.getElementById("status");
var statsEl = document.getElementById("stats");
var searchBox = document.getElementById("searchBox");
var searchButton = document.getElementById("searchButton");
var resetButton = document.getElementById("resetButton");
var modeSelect = document.getElementById("mode");
var algorithmSelect = document.getElementById("algorithm");

L.marker(thuDucCenter).addTo(map).bindPopup("Trung tâm Thủ Đức");

function setStatus(message) {
  statusEl.textContent = message;
}

function clearStats() {
  statsEl.innerHTML = "";
}

function addStat(label, value) {
  var labelEl = document.createElement("div");
  var valueEl = document.createElement("div");

  labelEl.className = "muted";
  labelEl.textContent = label;
  valueEl.textContent = value;

  statsEl.appendChild(labelEl);
  statsEl.appendChild(valueEl);
}

function formatKm(meters) {
  return (meters / 1000).toFixed(2) + " km";
}

function formatMinutes(minutes) {
  if (minutes < 1) {
    return Math.max(1, Math.round(minutes * 60)) + " giây";
  }
  return minutes.toFixed(1) + " phút";
}

function algorithmLabel(value) {
  if (value === "astar") return "A*";
  if (value === "dijkstra") return "Dijkstra";
  return "A*";
}

function providerLabel(value) {
  if (value === "local-osmnx") return "OSMnx cục bộ";
  return value || "-";
}

function routeColor(algorithm) {
  if (algorithm === "dijkstra") return "#2563eb";
  return "#dc2626";
}

function setStartMarker(latlng) {
  if (startMarker) {
    map.removeLayer(startMarker);
  }

  startMarker = L.marker(latlng, { draggable: true })
    .addTo(map)
    .bindPopup("Điểm bắt đầu")
    .openPopup();

  startMarker.on("dragend", function () {
    if (endMarker) findRoute();
  });
}

function setEndMarker(latlng) {
  if (endMarker) {
    map.removeLayer(endMarker);
  }

  endMarker = L.marker(latlng, { draggable: true })
    .addTo(map)
    .bindPopup("Điểm kết thúc")
    .openPopup();

  endMarker.on("dragend", function () {
    if (startMarker) findRoute();
  });
}

function removeRouteLine() {
  if (routeLine) {
    map.removeLayer(routeLine);
    routeLine = null;
  }

  if (snapStartLine) {
    map.removeLayer(snapStartLine);
    snapStartLine = null;
  }

  if (snapEndLine) {
    map.removeLayer(snapEndLine);
    snapEndLine = null;
  }
}

function resetMap() {
  if (startMarker) map.removeLayer(startMarker);
  if (endMarker) map.removeLayer(endMarker);
  removeRouteLine();

  startMarker = null;
  endMarker = null;
  setStatus("Sẵn sàng");
  clearStats();
}

function searchLocation() {
  var query = searchBox.value.trim();
  if (!query) return;

  setStatus("Đang tìm địa điểm...");

  var params = new URLSearchParams({
    format: "json",
    q: query,
    limit: "1",
    bounded: "1",
    viewbox: "106.70,10.90,106.85,10.80",
    "accept-language": "vi",
  });

  fetch("https://nominatim.openstreetmap.org/search?" + params.toString())
    .then(function (res) {
      return res.json();
    })
    .then(function (data) {
      if (!data.length) {
        setStatus("Không tìm thấy địa điểm trong khu vực Thủ Đức.");
        return;
      }

      var lat = parseFloat(data[0].lat);
      var lon = parseFloat(data[0].lon);
      var latlng = [lat, lon];

      map.setView(latlng, 16);

      if (searchMarker) {
        map.removeLayer(searchMarker);
      }

      searchMarker = L.marker(latlng)
        .addTo(map)
        .bindPopup(data[0].display_name || "Kết quả tìm kiếm")
        .openPopup();

      setStatus("Đã tìm thấy địa điểm.");
    })
    .catch(function (err) {
      console.error(err);
      setStatus("Không thể tìm địa điểm.");
    });
}

map.on("click", function (e) {
  if (isRouting) return;

  if (!startMarker) {
    setStartMarker(e.latlng);
    setStatus("Đã chọn điểm bắt đầu.");
    clearStats();
    return;
  }

  if (!endMarker) {
    setEndMarker(e.latlng);
    findRoute();
    return;
  }

  resetMap();
  setStartMarker(e.latlng);
  setStatus("Đã chọn điểm bắt đầu mới.");
});

function findRoute() {
  if (!startMarker || !endMarker || isRouting) return;

  isRouting = true;
  removeRouteLine();
  clearStats();
  setStatus("Đang chạy " + algorithmLabel(algorithmSelect.value) + "...");

  fetch("/route", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      start_lat: startMarker.getLatLng().lat,
      start_lon: startMarker.getLatLng().lng,
      end_lat: endMarker.getLatLng().lat,
      end_lon: endMarker.getLatLng().lng,
      mode: modeSelect.value,
      algorithm: algorithmSelect.value,
    }),
  })
    .then(function (res) {
      return res.json();
    })
    .then(function (data) {
      if (data.error) {
        setStatus(data.error);
        return;
      }

      drawRoute(data.coords, data.algorithm);
      drawSnapLines(data);
      renderStats(data);

      if (typeof data.snap_distance === "number" && data.snap_distance > 80) {
        setStatus(
          "Tìm đường xong. Lưu ý: điểm chọn khá xa đường gần nhất trên bản đồ.",
        );
      } else {
        setStatus("Tìm đường xong.");
      }
    })
    .catch(function (err) {
      console.error(err);
      setStatus("Có lỗi khi tìm đường.");
    })
    .finally(function () {
      isRouting = false;
    });
}

function drawRoute(coords, algorithm) {
  if (!coords || coords.length === 0) {
    setStatus("Không có đường để vẽ.");
    return;
  }

  routeLine = L.polyline(coords, {
    color: routeColor(algorithm),
    weight: 5,
    opacity: 0.9,
  }).addTo(map);

  map.fitBounds(routeLine.getBounds(), { padding: [32, 32] });
}

function drawSnapLines(data) {
  if (!startMarker || !endMarker) return;

  if (data.snapped_start) {
    snapStartLine = L.polyline(
      [
        [startMarker.getLatLng().lat, startMarker.getLatLng().lng],
        data.snapped_start,
      ],
      {
        color: "#6b7280",
        weight: 3,
        opacity: 0.8,
        dashArray: "6, 6",
      },
    ).addTo(map);
  }

  if (data.snapped_end) {
    snapEndLine = L.polyline(
      [
        [endMarker.getLatLng().lat, endMarker.getLatLng().lng],
        data.snapped_end,
      ],
      {
        color: "#6b7280",
        weight: 3,
        opacity: 0.8,
        dashArray: "6, 6",
      },
    ).addTo(map);
  }
}

function renderStats(data) {
  clearStats();
  addStat("Thuật toán", algorithmLabel(data.algorithm));
  addStat("Nguồn", providerLabel(data.provider));
  addStat("Khoảng cách", formatKm(data.distance));
  addStat("Thời gian", formatMinutes(data.time));

  if (typeof data.visited_count === "number") {
    addStat("Node đã duyệt", data.visited_count.toLocaleString("vi-VN"));
  }

  if (typeof data.path_nodes === "number") {
    addStat("Node trên đường", data.path_nodes.toLocaleString("vi-VN"));
  }

  if (typeof data.max_frontier_size === "number") {
    addStat(
      "Frontier lớn nhất",
      data.max_frontier_size.toLocaleString("vi-VN"),
    );
  }

  if (typeof data.runtime_ms === "number") {
    addStat("Thời gian chạy", data.runtime_ms.toFixed(2) + " ms");
  }

  if (typeof data.snap_distance === "number") {
    addStat("Tổng sai số bám đường", data.snap_distance.toFixed(1) + " m");
  }

  if (typeof data.start_snap_distance === "number") {
    addStat("Lệch điểm đầu", data.start_snap_distance.toFixed(1) + " m");
  }

  if (typeof data.end_snap_distance === "number") {
    addStat("Lệch điểm cuối", data.end_snap_distance.toFixed(1) + " m");
  }
}

searchButton.addEventListener("click", searchLocation);
resetButton.addEventListener("click", resetMap);

searchBox.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    searchLocation();
  }
});

modeSelect.addEventListener("change", function () {
  if (startMarker && endMarker) findRoute();
});

algorithmSelect.addEventListener("change", function () {
  if (startMarker && endMarker) findRoute();
});
