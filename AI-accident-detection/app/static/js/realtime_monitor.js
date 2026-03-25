let realtimeMonitorMap = null;
let realtimeMonitorInfoWindow = null;
let realtimeMonitorMarkers = [];

async function fetchJson(url) {
    const response = await fetch(url, {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    });

    return await response.json();
}

function getMarkerIconByRiskLevel(riskLevel) {
    switch (riskLevel) {
        case "긴급":
            return "http://maps.google.com/mapfiles/ms/icons/red-dot.png";
        case "위험":
            return "http://maps.google.com/mapfiles/ms/icons/orange-dot.png";
        case "주의":
        default:
            return "http://maps.google.com/mapfiles/ms/icons/yellow-dot.png";
    }
}

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}

function clearMarkers() {
    realtimeMonitorMarkers.forEach(marker => marker.setMap(null));
    realtimeMonitorMarkers = [];
}

function buildInfoWindowContent(item) {
    return `
        <div class="map-info-window">
            <div class="map-info-title">${escapeHtml(item.location_text || "위치 정보 없음")}</div>
            <div class="map-info-row"><strong>위험도:</strong> ${escapeHtml(item.risk_level || "-")}</div>
            <div class="map-info-row"><strong>장애물:</strong> ${escapeHtml(item.detected_label || "-")}</div>
            <div class="map-info-row"><strong>접수 시간:</strong> ${escapeHtml(item.created_at || "-")}</div>
            <div class="map-info-row"><strong>처리 상태:</strong> ${escapeHtml(item.status || "-")}</div>
            <div class="map-info-row"><strong>신뢰도:</strong> ${escapeHtml(String(item.confidence ?? "-"))}</div>
        </div>
    `;
}

async function loadMapPoints() {
    if (!window.REALTIME_MONITOR_CONFIG || !realtimeMonitorMap) {
        return;
    }

    const result = await fetchJson(window.REALTIME_MONITOR_CONFIG.mapPointsApiUrl);
    if (!result.success) {
        return;
    }

    const items = result.items || [];
    clearMarkers();

    const bounds = new google.maps.LatLngBounds();
    let validCount = 0;

    items.forEach(item => {
        const lat = Number(item.latitude);
        const lng = Number(item.longitude);

        if (!lat || !lng) {
            return;
        }

        const marker = new google.maps.Marker({
            position: { lat, lng },
            map: realtimeMonitorMap,
            title: item.location_text || "위치 정보 없음",
            icon: getMarkerIconByRiskLevel(item.risk_level)
        });

        marker.addListener("click", () => {
            if (!realtimeMonitorInfoWindow) {
                realtimeMonitorInfoWindow = new google.maps.InfoWindow();
            }

            realtimeMonitorInfoWindow.setContent(buildInfoWindowContent(item));
            realtimeMonitorInfoWindow.open({
                anchor: marker,
                map: realtimeMonitorMap
            });
        });

        realtimeMonitorMarkers.push(marker);
        bounds.extend({ lat, lng });
        validCount += 1;
    });

    if (validCount > 0) {
        realtimeMonitorMap.fitBounds(bounds);

        // 지나치게 확대되는 것 방지
        const listener = google.maps.event.addListener(realtimeMonitorMap, "idle", function () {
            if (realtimeMonitorMap.getZoom() > 15) {
                realtimeMonitorMap.setZoom(15);
            }
            google.maps.event.removeListener(listener);
        });
    }
}

async function loadSummaryCards() {
    if (!window.REALTIME_MONITOR_CONFIG) {
        return;
    }

    const result = await fetchJson(window.REALTIME_MONITOR_CONFIG.summaryApiUrl);
    if (!result.success) {
        return;
    }

    const data = result.data || {};

    const currentRiskZones = document.getElementById("summary-current-risk-zones");
    const todayReports = document.getElementById("summary-today-reports");
    const emergencyLast24h = document.getElementById("summary-emergency-last-24h");
    const hotspots = document.getElementById("summary-hotspots");

    if (currentRiskZones) currentRiskZones.textContent = data.current_risk_zones ?? 0;
    if (todayReports) todayReports.textContent = data.today_reports ?? 0;
    if (emergencyLast24h) emergencyLast24h.textContent = data.emergency_last_24h ?? 0;
    if (hotspots) hotspots.textContent = data.hotspots ?? 0;
}

function createRiskListItem(item) {
    const wrapper = document.createElement("div");
    wrapper.className = `risk-list-item risk-${item.risk_level || "주의"}`;

    wrapper.innerHTML = `
        <div class="risk-list-top">
            <span class="risk-badge risk-${item.risk_level || "주의"}">${escapeHtml(item.risk_level || "주의")}</span>
            <span class="risk-time">${escapeHtml(item.time_ago || "-")}</span>
        </div>

        <div class="risk-location">${escapeHtml(item.location_text || "위치 정보 없음")}</div>

        <div class="risk-meta">
            <span>장애물: ${escapeHtml(item.detected_label || "-")}</span>
            <span>상태: ${escapeHtml(item.status || "-")}</span>
        </div>

        <div class="risk-extra">
            <span>신고ID: ${escapeHtml(String(item.report_id || "-"))}</span>
            <span>신뢰도: ${escapeHtml(String(item.confidence ?? "-"))}</span>
        </div>
    `;

    return wrapper;
}

async function loadRiskList() {
    if (!window.REALTIME_MONITOR_CONFIG) {
        return;
    }

    const result = await fetchJson(window.REALTIME_MONITOR_CONFIG.riskListApiUrl);
    if (!result.success) {
        return;
    }

    const items = result.items || [];
    const listContainer = document.getElementById("realtime-risk-list");

    if (!listContainer) {
        return;
    }

    listContainer.innerHTML = "";

    if (items.length === 0) {
        listContainer.innerHTML = `
            <div class="risk-empty-state">
                현재 표시할 위험 데이터가 없습니다.
            </div>
        `;
        return;
    }

    items.forEach(item => {
        listContainer.appendChild(createRiskListItem(item));
    });
}

async function refreshRealtimeMonitorData() {
    try {
        await Promise.all([
            loadSummaryCards(),
            loadMapPoints(),
            loadRiskList()
        ]);
    } catch (error) {
        console.error("실시간 위험 현황 데이터 갱신 실패:", error);
    }
}

function initRealtimeMonitorMap() {
    const mapElement = document.getElementById("realtime-monitor-map");
    if (!mapElement) {
        return;
    }

    realtimeMonitorMap = new google.maps.Map(mapElement, {
        center: { lat: 37.5665, lng: 126.9780 },
        zoom: 11,
        mapTypeControl: true,
        fullscreenControl: true,
        streetViewControl: false
    });

    realtimeMonitorInfoWindow = new google.maps.InfoWindow();

    refreshRealtimeMonitorData();

    // 15초마다 새로고침
    setInterval(refreshRealtimeMonitorData, 15000);
}

window.initRealtimeMonitorMap = initRealtimeMonitorMap;