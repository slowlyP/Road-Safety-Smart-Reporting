(function () {
    /**
     * 실시간 위험 알림 프론트 스크립트
     *
     * 현재 구조 기준
     * - base.html 에서 관리자 로그인 시 공통 로드
     * - sidebar badge 갱신
     * - toast 표시
     * - 실시간 알림 페이지에서는 테이블 tbody에 새 row prepend
     * - 읽음 처리 / 전체 읽음 처리 지원
     */

    const socketStatusEl = document.getElementById("socket-status");
    const toastContainerEl = document.getElementById("realtime-alert-toast-container");
    const tableBodyEl = document.getElementById("realtime-alert-tbody");
    const markAllBtn = document.getElementById("mark-all-alerts-read-btn");

    const unreadBadgeEls = document.querySelectorAll(".realtime-alert-badge");

    const dangerSoundEl = document.getElementById("sound-danger");
    const emergencySoundEl = document.getElementById("sound-emergency");

    // 현재 페이지가 실시간 알림 페이지인지 여부
    const isRealtimePage = !!tableBodyEl;

    // -------------------------------------------------------
    // 초기 디버깅 로그
    // -------------------------------------------------------
    console.log("[RealtimeAlert] dangerSoundEl:", dangerSoundEl);
    console.log("[RealtimeAlert] emergencySoundEl:", emergencySoundEl);
    console.log("[RealtimeAlert] isRealtimePage:", isRealtimePage);

    // -------------------------------------------------------
    // 공통 유틸
    // -------------------------------------------------------
    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function formatConfidence(value) {
        const num = Number(value ?? 0);
        return Number.isNaN(num) ? "0.00" : num.toFixed(2);
    }

    function updateUnreadBadge(count) {
        unreadBadgeEls.forEach((badge) => {
            if (!badge) return;

            if (count > 0) {
                badge.textContent = String(count);
                badge.style.display = "inline-flex";
            } else {
                badge.textContent = "0";
                badge.style.display = "none";
            }
        });
    }

    function setSocketStatus(text, className = "") {
        if (!socketStatusEl) return;
        socketStatusEl.textContent = text;
        socketStatusEl.className = className;
    }

    function playAlertSound(level) {
        try {
            if (level === "긴급") {
                if (!emergencySoundEl) {
                    console.warn("[RealtimeAlert] 긴급 사운드 태그를 찾지 못했습니다.");
                    return;
                }

                console.log("[RealtimeAlert] 긴급 사운드 재생 시도");
                emergencySoundEl.currentTime = 0;
                emergencySoundEl.play().catch((err) => {
                    console.warn("[RealtimeAlert] 긴급 사운드 재생 실패:", err);
                });
                return;
            }

            if (level === "위험") {
                if (!dangerSoundEl) {
                    console.warn("[RealtimeAlert] 위험 사운드 태그를 찾지 못했습니다.");
                    return;
                }

                console.log("[RealtimeAlert] 위험 사운드 재생 시도");
                dangerSoundEl.currentTime = 0;
                dangerSoundEl.play().catch((err) => {
                    console.warn("[RealtimeAlert] 위험 사운드 재생 실패:", err);
                });
            }
        } catch (err) {
            console.warn("[RealtimeAlert] 알림 사운드 재생 예외:", err);
        }
    }

    function levelClass(level) {
        return level === "긴급" ? "emergency" : "danger";
    }

    // -------------------------------------------------------
    // Toast
    // -------------------------------------------------------
    function showToast(alertData) {
        if (!toastContainerEl) return;

        const level = alertData.alert_level || alertData.risk_level || "위험";
        const toast = document.createElement("div");
        toast.className = `realtime-alert-toast ${level === "긴급" ? "emergency" : "danger"}`;

        toast.innerHTML = `
            <div class="realtime-alert-toast-header">
                <span>[${escapeHtml(level)}] 실시간 위험 알림</span>
                <button type="button" class="realtime-alert-toast-close" aria-label="닫기">×</button>
            </div>
            <div class="realtime-alert-toast-body">
                <div class="realtime-alert-toast-message">
                    ${escapeHtml(alertData.message || "")}
                </div>
                <div class="realtime-alert-toast-meta">
                    <div><strong>신고 제목:</strong> ${escapeHtml(alertData.report_title || alertData.title || "-")}</div>
                    <div><strong>위치:</strong> ${escapeHtml(alertData.location_text || "-")}</div>
                    <div><strong>탐지 객체:</strong> ${escapeHtml(alertData.detected_label || "-")}</div>
                    <div><strong>발생 시각:</strong> ${escapeHtml(alertData.created_at || "-")}</div>
                </div>
                <div class="realtime-alert-toast-actions">
                    <a href="/admin/reports/${alertData.report_id}" class="realtime-alert-toast-link">
                        상세보기
                    </a>
                </div>
            </div>
        `;

        toastContainerEl.prepend(toast);

        requestAnimationFrame(() => {
            toast.classList.add("show");
        });

        const closeBtn = toast.querySelector(".realtime-alert-toast-close");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                removeToast(toast);
            });
        }

        setTimeout(() => {
            removeToast(toast);
        }, 5000);
    }

    function removeToast(toastEl) {
        if (!toastEl) return;

        toastEl.classList.remove("show");

        setTimeout(() => {
            if (toastEl.parentNode) {
                toastEl.parentNode.removeChild(toastEl);
            }
        }, 300);
    }

    // -------------------------------------------------------
    // 테이블 row 생성 / 추가
    // -------------------------------------------------------
    function buildAlertMainRow(alertData) {
        const tr = document.createElement("tr");
        tr.className = "unread";
        tr.dataset.alertId = alertData.alert_id;
        tr.dataset.alertLevel = alertData.alert_level || alertData.risk_level || "위험";

        const level = alertData.alert_level || alertData.risk_level || "위험";
        const levelCls = levelClass(level);

        tr.innerHTML = `
            <td>
                <span class="alert-level-badge ${levelCls}">
                    ${escapeHtml(level)}
                </span>
            </td>
            <td>${escapeHtml(alertData.message || "")}</td>
            <td>${escapeHtml(alertData.report_title || alertData.title || "-")}</td>
            <td>${escapeHtml(alertData.location_text || "-")}</td>
            <td>${escapeHtml(alertData.detected_label || "-")}</td>
            <td>${formatConfidence(alertData.confidence)}</td>
            <td>${escapeHtml(alertData.created_at || "-")}</td>
            <td>
                <a href="/admin/reports/${alertData.report_id}" class="realtime-alert-toast-link">
                    상세보기
                </a>
            </td>
            <td>
                <button
                    type="button"
                    class="mark-read-btn btn-mark-read"
                    data-alert-id="${alertData.alert_id}"
                >
                    읽음 처리
                </button>
            </td>
        `;

        return tr;
    }

    function buildAlertImageRow(alertData) {
        if (!alertData.file_path) return null;

        const tr = document.createElement("tr");
        tr.className = "unread";
        tr.dataset.alertImageRow = "true";
        tr.dataset.parentAlertId = alertData.alert_id;

        tr.innerHTML = `
            <td colspan="9" style="padding-top: 0;">
                <div style="padding: 8px 0;">
                    <img
                        src="${escapeHtml(alertData.file_path)}"
                        alt="탐지 이미지"
                        style="max-width: 240px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);"
                    >
                </div>
            </td>
        `;

        return tr;
    }

    function prependAlertRows(alertData) {
        if (!tableBodyEl) return;

        // -------------------------------------------------------
        // [보강] 같은 alert_id가 이미 있으면 중복 추가 방지
        // -------------------------------------------------------
        const exists = tableBodyEl.querySelector(
            `tr[data-alert-id="${alertData.alert_id}"]`
        );

        if (exists) {
            console.log("[RealtimeAlert] 중복 알림 감지 - row 추가 생략:", alertData.alert_id);
            return;
        }

        const mainRow = buildAlertMainRow(alertData);
        const imageRow = buildAlertImageRow(alertData);

        if (imageRow) {
            tableBodyEl.prepend(imageRow);
        }
        tableBodyEl.prepend(mainRow);
    }

    function markRowsAsRead(alertId) {
        if (!tableBodyEl) return;

        const mainRow = tableBodyEl.querySelector(`tr[data-alert-id="${alertId}"]`);
        if (mainRow) {
            mainRow.classList.remove("unread");

            const btn = mainRow.querySelector(".btn-mark-read");
            if (btn) {
                btn.disabled = true;
                btn.textContent = "읽음 완료";
            }
        }

        const imageRow = tableBodyEl.querySelector(`tr[data-parent-alert-id="${alertId}"]`);
        if (imageRow) {
            imageRow.classList.remove("unread");
        }
    }

    function markAllRowsAsRead() {
        if (!tableBodyEl) return;

        const unreadRows = tableBodyEl.querySelectorAll("tr.unread");
        unreadRows.forEach((row) => {
            row.classList.remove("unread");
        });

        const buttons = tableBodyEl.querySelectorAll(".btn-mark-read");
        buttons.forEach((btn) => {
            btn.disabled = true;
            btn.textContent = "읽음 완료";
        });
    }

    // -------------------------------------------------------
    // API
    // -------------------------------------------------------
    async function fetchUnreadCount() {
        try {
            const response = await fetch("/admin/realtime-alerts/unread-count", {
                method: "GET",
                credentials: "same-origin"
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                console.warn("[RealtimeAlert] 미확인 개수 조회 실패:", data);
                return;
            }

            updateUnreadBadge(data.unread_count || 0);
        } catch (err) {
            console.warn("[RealtimeAlert] 미확인 개수 조회 오류:", err);
        }
    }

    async function markAlertAsRead(alertId) {
        try {
            const response = await fetch(`/admin/realtime-alerts/${alertId}/read`, {
                method: "PATCH",
                credentials: "same-origin"
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                console.warn("[RealtimeAlert] 읽음 처리 실패:", data);
                return;
            }

            markRowsAsRead(alertId);
            updateUnreadBadge(data.unread_count || 0);
        } catch (err) {
            console.warn("[RealtimeAlert] 읽음 처리 오류:", err);
        }
    }

    async function markAllAlertsAsRead() {
        try {
            const response = await fetch("/admin/realtime-alerts/read-all", {
                method: "PATCH",
                credentials: "same-origin"
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                console.warn("[RealtimeAlert] 전체 읽음 처리 실패:", data);
                return;
            }

            markAllRowsAsRead();
            updateUnreadBadge(data.unread_count || 0);
        } catch (err) {
            console.warn("[RealtimeAlert] 전체 읽음 처리 오류:", err);
        }
    }

    // -------------------------------------------------------
    // 소켓 연결
    // -------------------------------------------------------
    const socket = io("/admin/realtime-alert");

    socket.on("connect", () => {
        setSocketStatus("연결됨", "connected");
        console.log("[RealtimeAlert] socket connected");
    });

    socket.on("disconnect", () => {
        setSocketStatus("연결 끊김", "disconnected");
        console.log("[RealtimeAlert] socket disconnected");
    });

    socket.on("connect_error", (err) => {
        setSocketStatus("연결 오류", "error");
        console.warn("[RealtimeAlert] socket connect error:", err);
    });

    // -------------------------------------------------------
    // 서버 emit 이벤트명과 반드시 동일해야 함
    // -------------------------------------------------------
    socket.on("new_realtime_alert", (data) => {
        console.log("[RealtimeAlert] new alert:", data);

        const level = data.alert_level || data.risk_level || "위험";

        // 1) 토스트 표시
        showToast(data);

        // 2) 사운드 재생
        playAlertSound(level);

        // 3) 실시간 알림 페이지면 tbody 맨 위에 row 추가
        if (isRealtimePage) {
            prependAlertRows(data);
        }

        // 4) unread badge 갱신
        fetchUnreadCount();
    });

    // -------------------------------------------------------
    // 이벤트 위임
    // -------------------------------------------------------
    document.addEventListener("click", (event) => {
        const markReadBtn = event.target.closest(".btn-mark-read");
        if (markReadBtn) {
            const alertId = markReadBtn.dataset.alertId;
            if (alertId) {
                markAlertAsRead(alertId);
            }
        }
    });

    if (markAllBtn) {
        markAllBtn.addEventListener("click", () => {
            markAllAlertsAsRead();
        });
    }

    // -------------------------------------------------------
    // 초기 실행
    // -------------------------------------------------------
    fetchUnreadCount();
})();