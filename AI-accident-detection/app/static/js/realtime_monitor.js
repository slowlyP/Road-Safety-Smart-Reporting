let realtimeMonitorMap = null;
let realtimeMonitorInfoWindow = null;
let realtimeMonitorMarkers = [];

// 원본 데이터 저장
let ALL_MAP_POINTS = [];
let ALL_RISK_LIST = [];

// 현재 필터 상태
let CURRENT_RISK_FILTER = "all";
let CURRENT_USER_POSITION = null;
let CURRENT_RADIUS_KM = 3;

async function fetchJson(url) {
    const response = await fetch(url, {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    });

    return await response.json();
}

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
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

function clearMarkers() {
    realtimeMonitorMarkers.forEach((marker) => marker.setMap(null));
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
            <div class="map-info-row" style="margin-top: 10px;">
                <button type="button" class="map-detail-btn" data-report-id="${item.report_id}">
                    상세보기
                </button>
            </div>
        </div>
    `;
}

function createRiskListItem(item) {
    const wrapper = document.createElement("div");
    wrapper.className = `risk-list-item risk-${item.risk_level || "주의"}`;
    wrapper.dataset.reportId = item.report_id || "";

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

    wrapper.addEventListener("click", () => {
        if (item.report_id) {
            openRiskDetailModal(item.report_id);
        }
    });

    return wrapper;
}

function haversineDistanceKm(lat1, lng1, lat2, lng2) {
    const toRad = (deg) => deg * (Math.PI / 180);
    const R = 6371;

    const dLat = toRad(lat2 - lat1);
    const dLng = toRad(lng2 - lng1);

    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
        Math.sin(dLng / 2) * Math.sin(dLng / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function matchesRiskFilter(item) {
    if (CURRENT_RISK_FILTER === "all") {
        return true;
    }
    return item.risk_level === CURRENT_RISK_FILTER;
}

function matchesNearbyFilter(item) {
    if (!CURRENT_USER_POSITION) {
        return true;
    }

    const lat = Number(item.latitude);
    const lng = Number(item.longitude);

    if (!lat || !lng) {
        return false;
    }

    const distance = haversineDistanceKm(
        CURRENT_USER_POSITION.lat,
        CURRENT_USER_POSITION.lng,
        lat,
        lng
    );

    return distance <= CURRENT_RADIUS_KM;
}

function getFilteredMapPoints() {
    return ALL_MAP_POINTS.filter((item) => {
        return matchesRiskFilter(item) && matchesNearbyFilter(item);
    });
}

function getFilteredRiskList() {
    return ALL_RISK_LIST.filter((item) => {
        if (!matchesRiskFilter(item)) {
            return false;
        }

        if (CURRENT_USER_POSITION) {
            const matched = ALL_MAP_POINTS.find((p) => p.report_id === item.report_id);
            if (!matched) return false;
            return matchesNearbyFilter(matched);
        }

        return true;
    });
}

function updateFilterStatus() {
    const statusEl = document.getElementById("monitor-filter-status");
    if (!statusEl) return;

    const riskText = CURRENT_RISK_FILTER === "all" ? "전체 위험도" : `${CURRENT_RISK_FILTER}만`;
    const nearbyText = CURRENT_USER_POSITION
        ? `내 주변 반경 ${CURRENT_RADIUS_KM}km 기준으로`
        : "전체 지역 기준으로";

    statusEl.textContent = `${nearbyText} ${riskText} 표시하고 있습니다.`;
}

function renderMapPoints(points) {
    if (!realtimeMonitorMap) return;

    clearMarkers();

    const bounds = new google.maps.LatLngBounds();
    let validCount = 0;

    points.forEach((item) => {
        const lat = Number(item.latitude);
        const lng = Number(item.longitude);

        if (!lat || !lng) return;

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

            google.maps.event.addListenerOnce(realtimeMonitorInfoWindow, "domready", () => {
                const btn = document.querySelector(".map-detail-btn");
                if (btn) {
                    btn.addEventListener("click", () => openRiskDetailModal(item.report_id));
                }
            });
        });

        realtimeMonitorMarkers.push(marker);
        bounds.extend({ lat, lng });
        validCount += 1;
    });

    if (CURRENT_USER_POSITION) {
        const userMarker = new google.maps.Marker({
            position: CURRENT_USER_POSITION,
            map: realtimeMonitorMap,
            title: "내 현재 위치",
            icon: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png"
        });

        realtimeMonitorMarkers.push(userMarker);
        bounds.extend(CURRENT_USER_POSITION);
        validCount += 1;
    }

    if (validCount > 0) {
        realtimeMonitorMap.fitBounds(bounds);

        const listener = google.maps.event.addListener(realtimeMonitorMap, "idle", function () {
            if (realtimeMonitorMap.getZoom() > 15) {
                realtimeMonitorMap.setZoom(15);
            }
            google.maps.event.removeListener(listener);
        });
    }
}

function renderRiskList(items) {
    const listContainer = document.getElementById("realtime-risk-list");
    if (!listContainer) return;

    listContainer.innerHTML = "";

    if (items.length === 0) {
        listContainer.innerHTML = `
            <div class="risk-empty-state">
                현재 조건에 맞는 위험 데이터가 없습니다.
            </div>
        `;
        return;
    }

    items.forEach((item) => {
        listContainer.appendChild(createRiskListItem(item));
    });
}

function applyFiltersAndRender() {
    const filteredMapPoints = getFilteredMapPoints();
    const filteredRiskList = getFilteredRiskList();

    renderMapPoints(filteredMapPoints);
    renderRiskList(filteredRiskList);
    updateFilterStatus();
}

async function loadMapPoints() {
    if (!window.REALTIME_MONITOR_CONFIG) return;

    const result = await fetchJson(window.REALTIME_MONITOR_CONFIG.mapPointsApiUrl);
    if (!result.success) return;

    ALL_MAP_POINTS = result.items || [];
}

async function loadSummaryCards() {
    if (!window.REALTIME_MONITOR_CONFIG) return;

    const result = await fetchJson(window.REALTIME_MONITOR_CONFIG.summaryApiUrl);
    if (!result.success) return;

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

async function loadRiskList() {
    if (!window.REALTIME_MONITOR_CONFIG) return;

    const result = await fetchJson(window.REALTIME_MONITOR_CONFIG.riskListApiUrl);
    if (!result.success) return;

    ALL_RISK_LIST = result.items || [];
}

async function refreshRealtimeMonitorData() {
    try {
        await Promise.all([
            loadSummaryCards(),
            loadMapPoints(),
            loadRiskList()
        ]);

        applyFiltersAndRender();
    } catch (error) {
        console.error("탐지 현황 데이터 갱신 실패:", error);
    }
}

function bindRiskFilterButtons() {
    const buttons = document.querySelectorAll(".filter-btn[data-risk-filter]");
    buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
            buttons.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");

            CURRENT_RISK_FILTER = btn.dataset.riskFilter || "all";
            applyFiltersAndRender();
        });
    });
}

function bindRadiusSelect() {
    const radiusSelect = document.getElementById("nearby-radius-select");
    if (!radiusSelect) return;

    radiusSelect.addEventListener("change", () => {
        CURRENT_RADIUS_KM = Number(radiusSelect.value || 3);
        if (CURRENT_USER_POSITION) {
            applyFiltersAndRender();
        }
    });
}

function bindNearbyButtons() {
    const findBtn = document.getElementById("find-nearby-risk-btn");
    const resetBtn = document.getElementById("reset-nearby-risk-btn");

    if (findBtn) {
        findBtn.addEventListener("click", () => {
            if (!navigator.geolocation) {
                alert("이 브라우저에서는 위치 기능을 지원하지 않습니다.");
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    CURRENT_USER_POSITION = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    applyFiltersAndRender();
                },
                (error) => {
                    console.error("현재 위치 조회 실패:", error);
                    alert("현재 위치를 가져오지 못했습니다. 위치 권한을 확인해주세요.");
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            CURRENT_USER_POSITION = null;
            applyFiltersAndRender();
        });
    }
}

function initRealtimeMonitorMap() {
    const mapElement = document.getElementById("realtime-monitor-map");
    if (!mapElement) return;

    realtimeMonitorMap = new google.maps.Map(mapElement, {
        center: { lat: 37.5665, lng: 126.9780 },
        zoom: 11,
        mapTypeControl: true,
        fullscreenControl: true,
        streetViewControl: false
    });

    realtimeMonitorInfoWindow = new google.maps.InfoWindow();

    refreshRealtimeMonitorData();
    setInterval(refreshRealtimeMonitorData, 15000);
}

/* =========================
   상세 모달
========================= */

function getRiskDetailElements() {
    return {
        modal: document.getElementById("risk-detail-modal"),
        backdrop: document.getElementById("risk-detail-backdrop"),
        closeBtn: document.getElementById("risk-detail-close"),

        badge: document.getElementById("risk-detail-badge"),
        timeago: document.getElementById("risk-detail-timeago"),
        title: document.getElementById("risk-detail-title"),
        location: document.getElementById("risk-detail-location"),
        content: document.getElementById("risk-detail-content"),

        reportId: document.getElementById("risk-detail-report-id"),
        detectedLabel: document.getElementById("risk-detail-detected-label"),
        confidence: document.getElementById("risk-detail-confidence"),
        status: document.getElementById("risk-detail-status"),
        reportType: document.getElementById("risk-detail-report-type"),
        createdAt: document.getElementById("risk-detail-created-at"),
        fileType: document.getElementById("risk-detail-file-type"),
        originalName: document.getElementById("risk-detail-original-name"),

        image: document.getElementById("risk-detail-image"),
        imageEmpty: document.getElementById("risk-detail-image-empty"),
    };
}

function openModal() {
    const { modal } = getRiskDetailElements();
    if (!modal) return;

    modal.classList.remove("hidden");
    document.body.classList.add("modal-open");
}

function closeModal() {
    const { modal } = getRiskDetailElements();
    if (!modal) return;

    modal.classList.add("hidden");
    document.body.classList.remove("modal-open");
}

function setBadgeStyle(element, riskLevel) {
    if (!element) return;

    element.className = "risk-detail-badge";
    if (riskLevel === "긴급") {
        element.classList.add("emergency");
    } else if (riskLevel === "위험") {
        element.classList.add("danger");
    } else {
        element.classList.add("warning");
    }

    element.textContent = riskLevel || "주의";
}

function renderRiskDetail(detail) {
    const els = getRiskDetailElements();

    setBadgeStyle(els.badge, detail.risk_level);
    if (els.timeago) els.timeago.textContent = detail.time_ago || "-";
    if (els.title) els.title.textContent = detail.title || "제목 없음";
    if (els.location) els.location.textContent = detail.location_text || "위치 정보 없음";
    if (els.content) els.content.textContent = detail.content || "상세 내용 없음";

    if (els.reportId) els.reportId.textContent = detail.report_id ?? "-";
    if (els.detectedLabel) els.detectedLabel.textContent = detail.detected_label || "-";
    if (els.confidence) els.confidence.textContent = detail.confidence ?? "-";
    if (els.status) els.status.textContent = detail.status || "-";
    if (els.reportType) els.reportType.textContent = detail.report_type || "-";
    if (els.createdAt) els.createdAt.textContent = detail.created_at || "-";
    if (els.fileType) els.fileType.textContent = detail.file_type || "-";
    if (els.originalName) els.originalName.textContent = detail.original_name || "-";

    if (els.image && els.imageEmpty) {
        if (detail.file_path && detail.file_type === "이미지") {
            els.image.src = detail.file_path;
            els.image.style.display = "block";
            els.imageEmpty.style.display = "none";
        } else {
            els.image.src = "";
            els.image.style.display = "none";
            els.imageEmpty.style.display = "flex";
        }
    }
}

async function openRiskDetailModal(reportId) {
    if (!window.REALTIME_MONITOR_CONFIG || !reportId) return;

    try {
        const url = `${window.REALTIME_MONITOR_CONFIG.detailApiBaseUrl}/${reportId}`;
        const result = await fetchJson(url);

        if (!result.success) {
            alert(result.message || "상세 정보를 불러오지 못했습니다.");
            return;
        }

        renderRiskDetail(result.data);
        openModal();
    } catch (error) {
        console.error("상세 정보 조회 실패:", error);
        alert("상세 정보를 불러오는 중 오류가 발생했습니다.");
    }
}

function bindRiskDetailModalEvents() {
    const { backdrop, closeBtn, modal } = getRiskDetailElements();

    if (backdrop) {
        backdrop.addEventListener("click", closeModal);
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", closeModal);
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && modal && !modal.classList.contains("hidden")) {
            closeModal();
        }
    });

    document.querySelectorAll(".risk-list-item[data-report-id]").forEach((item) => {
        item.addEventListener("click", () => {
            const reportId = item.dataset.reportId;
            if (reportId) {
                openRiskDetailModal(reportId);
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindRiskFilterButtons();
    bindRadiusSelect();
    bindNearbyButtons();
    bindRiskDetailModalEvents();
});

window.initRealtimeMonitorMap = initRealtimeMonitorMap;