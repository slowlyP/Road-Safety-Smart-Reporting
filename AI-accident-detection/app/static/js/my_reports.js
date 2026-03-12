document.addEventListener("DOMContentLoaded", async () => {
  await loadMyReports();
});

async function loadMyReports() {
  const reportList = document.getElementById("report-list");
  const emptyBox = document.getElementById("empty-box");

  try {
    const response = await fetch("/reports/my", {
      method: "GET",
      credentials: "include"
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      emptyBox.style.display = "block";
      emptyBox.textContent = result.message || "신고 목록을 불러오지 못했습니다.";
      return;
    }

    const reports = result.data || [];

    updateSummary(reports);

    if (reports.length === 0) {
      emptyBox.style.display = "block";
      return;
    }

    reportList.innerHTML = reports.map(report => createReportCard(report)).join("");
  } catch (error) {
    emptyBox.style.display = "block";
    emptyBox.textContent = "서버와 통신 중 오류가 발생했습니다.";
  }
}

function updateSummary(reports) {
  const total = reports.length;
  const received = reports.filter(r => r.status === "접수").length;
  const checking = reports.filter(r => r.status === "확인중").length;
  const done = reports.filter(r => r.status === "처리완료").length;

  document.getElementById("total-count").textContent = total;
  document.getElementById("count-received").textContent = received;
  document.getElementById("count-checking").textContent = checking;
  document.getElementById("count-done").textContent = done;
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

      <div class="report-meta">
        <span class="meta-badge badge-type">${escapeHtml(report.report_type || "-")}</span>
        <span class="meta-badge badge-location">${escapeHtml(report.location_text || "위치 정보 없음")}</span>
        <span class="meta-badge ${getRiskClass(report.risk_level)}">${escapeHtml(report.risk_level || "-")}</span>
        <span class="meta-badge ${getStatusClass(report.status)}">${escapeHtml(report.status || "-")}</span>
      </div>
    </article>
  `;
}

function getRiskClass(riskLevel) {
  if (riskLevel === "낮음") return "badge-risk-low";
  if (riskLevel === "주의") return "badge-risk-mid";
  if (riskLevel === "위험") return "badge-risk-high";
  if (riskLevel === "긴급") return "badge-risk-urgent";
  return "badge-location";
}

function getStatusClass(status) {
  if (status === "접수") return "badge-status-received";
  if (status === "확인중") return "badge-status-checking";
  if (status === "처리완료") return "badge-status-done";
  if (status === "오탐") return "badge-status-false";
  return "badge-location";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}