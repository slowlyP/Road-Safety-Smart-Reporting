document.addEventListener("DOMContentLoaded", async () => {
  await loadMyReports();
});

async function loadMyReports() {
  const reportList = document.getElementById("report-list");
  const emptyBox = document.getElementById("empty-box");
  const todayDetectList = document.getElementById("today-detect-list");
  const todayDetectEmpty = document.getElementById("today-detect-empty");

  try {
    const response = await fetch("/reports/my", {
      method: "GET",
      credentials: "include"
    });

    const result = await response.json();

    if (!response.ok) {
      reportList.innerHTML = "";
      emptyBox.style.display = "block";
      emptyBox.textContent = result.message || "신고 목록을 불러오지 못했습니다.";

      if (todayDetectList) {
        todayDetectList.innerHTML = "";
      }
      if (todayDetectEmpty) {
        todayDetectEmpty.style.display = "block";
        todayDetectEmpty.textContent = result.message || "오늘 탐지 기록을 불러오지 못했습니다.";
      }
      return;
    }

    const reports = result.data || [];

    updateSummary(reports);
    renderTodayDetect(reports);

    if (reports.length === 0) {
      reportList.innerHTML = "";
      emptyBox.style.display = "block";
      emptyBox.textContent = "등록한 신고가 없습니다.";
      return;
    }

    emptyBox.style.display = "none";
    reportList.innerHTML = reports.map(report => createReportCard(report)).join("");

  } catch (error) {
    reportList.innerHTML = "";
    emptyBox.style.display = "block";
    emptyBox.textContent = "서버와 통신 중 오류가 발생했습니다.";

    const todayDetectList = document.getElementById("today-detect-list");
    const todayDetectEmpty = document.getElementById("today-detect-empty");

    if (todayDetectList) {
      todayDetectList.innerHTML = "";
    }
    if (todayDetectEmpty) {
      todayDetectEmpty.style.display = "block";
      todayDetectEmpty.textContent = "오늘 탐지 기록을 불러오지 못했습니다.";
    }

    console.error(error);
  }
}

function updateSummary(reports) {
  const total = reports.length;
  const received = reports.filter(report => report.status === "접수").length;
  const checking = reports.filter(report => report.status === "확인중").length;
  const done = reports.filter(
    report => report.status === "처리완료" || report.status === "처리 완료"
  ).length;

  document.getElementById("total-count").textContent = total;
  document.getElementById("count-received").textContent = received;
  document.getElementById("count-checking").textContent = checking;
  document.getElementById("count-done").textContent = done;
}

function renderTodayDetect(reports) {
  const todayDetectList = document.getElementById("today-detect-list");
  const todayDetectEmpty = document.getElementById("today-detect-empty");

  if (!todayDetectList || !todayDetectEmpty) {
    return;
  }

  const todayReports = reports
    .filter(report => isToday(report.created_at))
    .slice(0, 3);

  if (todayReports.length === 0) {
    todayDetectList.innerHTML = "";
    todayDetectEmpty.style.display = "block";
    todayDetectEmpty.textContent = "오늘 등록된 신고가 없습니다.";
    return;
  }

  todayDetectEmpty.style.display = "none";
  todayDetectList.innerHTML = todayReports
    .map(report => createTodayDetectItem(report))
    .join("");
}

function createTodayDetectItem(report) {
  const title = escapeHtml(report.title || "-");
  const location = escapeHtml(report.location_text || "위치 정보 없음");
  const time = escapeHtml(extractTime(report.created_at || "-"));
  const riskClass = getRiskClass(report.status);
  const riskLabel = getRiskLabel(report.status);

  return `
    <div class="detect-item">
      <span class="detect-time">${time}</span>

      <div class="detect-text">
        <strong>${title}</strong>
        <p>${location}</p>
      </div>

      <span class="badge ${riskClass}">${riskLabel}</span>
    </div>
  `;
}

function createReportCard(report) {
  return `
    <article class="report-card">
      <div class="report-top">
        <h3 class="report-title">${escapeHtml(report.title || "-")}</h3>
        <div class="report-date">${escapeHtml(report.created_at || "-")}</div>
      </div>

      <div class="report-content">
        ${escapeHtml(report.content || "내용이 없습니다.")}
      </div>

      <div class="report-meta-row">
        <div class="report-meta">
          <span class="meta-badge badge-type">${escapeHtml(report.file_type || "일반")}</span>
          <span class="meta-badge badge-location">${escapeHtml(report.location_text || "위치 정보 없음")}</span>
          <span class="meta-badge ${getStatusClass(report.status)}">${escapeHtml(report.status || "-")}</span>
        </div>

        <a href="/reports/${report.id}/page" class="detail-btn">상세보기</a>
      </div>
    </article>
  `;
}

function getStatusClass(status) {
  if (status === "접수") return "badge-status-received";
  if (status === "확인중") return "badge-status-checking";
  if (status === "처리완료" || status === "처리 완료") return "badge-status-done";
  if (status === "오탐") return "badge-status-false";
  return "badge-location";
}

function getRiskClass(status) {
  if (status === "처리완료" || status === "처리 완료") return "safe";
  if (status === "확인중") return "warning";
  if (status === "오탐") return "safe";
  return "danger";
}

function getRiskLabel(status) {
  if (status === "처리완료" || status === "처리 완료") return "저위험";
  if (status === "확인중") return "중위험";
  if (status === "오탐") return "저위험";
  return "고위험";
}

function isToday(createdAt) {
  if (!createdAt) return false;

  const dateOnly = createdAt.split(" ")[0];
  const today = new Date();

  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");
  const todayStr = `${yyyy}-${mm}-${dd}`;

  return dateOnly === todayStr;
}

function extractTime(createdAt) {
  if (!createdAt) return "-";

  const parts = createdAt.split(" ");
  if (parts.length < 2) return createdAt;

  const timeParts = parts[1].split(":");
  if (timeParts.length >= 2) {
    return `${timeParts[0]}:${timeParts[1]}`;
  }

  return parts[1];
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}