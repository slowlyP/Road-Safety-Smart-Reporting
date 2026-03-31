let currentPage = 1; // 현재 페이지 저장
const perPage = 5;   // 한 페이지당 5개

document.addEventListener("DOMContentLoaded", async () => {
  await loadMyReports(1);
});

async function loadMyReports(page = 1) { // 신고 목록 + 페이징 데이터 불러오기
  const reportList = document.getElementById("report-list");
  const emptyBox = document.getElementById("empty-box");
  const todayDetectList = document.getElementById("today-detect-list");
  const todayDetectEmpty = document.getElementById("today-detect-empty");
  const paginationBox = document.getElementById("pagination");

  try {
    const response = await fetch(`/reports/my?page=${page}&per_page=${perPage}`, {
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

      if (paginationBox) {
        paginationBox.innerHTML = "";
      }

      return;
    }

    const reports = result.data?.reports || [];
    const pagination = result.data?.pagination || {
      page: 1,
      total_pages: 1,
      has_prev: false,
      has_next: false
    };

    currentPage = pagination.page;

    updateSummary(reports);       // 상단 통계 업데이트
    renderTodayDetect(reports);   // 오늘 탐지 기록 렌더링

    if (reports.length === 0) {
      reportList.innerHTML = "";
      emptyBox.style.display = "block";
      emptyBox.textContent = "등록한 신고가 없습니다.";

      if (paginationBox) {
        paginationBox.innerHTML = "";
      }

      return;
    }

    emptyBox.style.display = "none";
    reportList.innerHTML = reports.map(report => createReportCard(report)).join("");

    renderPagination(pagination); // 페이지 버튼 렌더링

  } catch (error) {
    reportList.innerHTML = "";
    emptyBox.style.display = "block";
    emptyBox.textContent = "서버와 통신 중 오류가 발생했습니다.";

    if (todayDetectList) {
      todayDetectList.innerHTML = "";
    }

    if (todayDetectEmpty) {
      todayDetectEmpty.style.display = "block";
      todayDetectEmpty.textContent = "오늘 탐지 기록을 불러오지 못했습니다.";
    }

    if (paginationBox) {
      paginationBox.innerHTML = "";
    }

    console.error(error);
  }
}

function renderPagination(pagination) { // 페이지 버튼 생성
  const paginationBox = document.getElementById("pagination");
  if (!paginationBox) return;

  paginationBox.innerHTML = "";

  const { page, total_pages, has_prev, has_next } = pagination;

  if (total_pages <= 1) return;

  let html = "";

  html += `
    <button
      class="page-btn nav-btn prev-btn"
      ${!has_prev ? "disabled" : ""}
      onclick="loadMyReports(${page - 1})"
    >
      이전
    </button>
  `;

  const pages = getPageNumbers(page, total_pages);

  pages.forEach((item) => {
    if (item === "...") {
      html += `<span class="page-ellipsis">...</span>`;
    } else {
      html += `
        <button
          class="page-btn number-btn ${item === page ? "active" : ""}"
          onclick="loadMyReports(${item})"
        >
          ${item}
        </button>
      `;
    }
  });

  html += `
    <button
      class="page-btn nav-btn next-btn"
      ${!has_next ? "disabled" : ""}
      onclick="loadMyReports(${page + 1})"
    >
      다음
    </button>
  `;

  paginationBox.innerHTML = html;
}

function getPageNumbers(currentPage, totalPages) { // 10페이지 이상일 때 ... 처리
  const pages = [];

  if (totalPages <= 10) {
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i);
    }
    return pages;
  }

  if (currentPage <= 5) {
    pages.push(1, 2, 3, 4, 5, 6, 7, "...", totalPages);
    return pages;
  }

  if (currentPage >= totalPages - 4) {
    pages.push(1, "...");
    for (let i = totalPages - 6; i <= totalPages; i++) {
      pages.push(i);
    }
    return pages;
  }

  pages.push(
    1,
    "...",
    currentPage - 2,
    currentPage - 1,
    currentPage,
    currentPage + 1,
    currentPage + 2,
    "...",
    totalPages
  );

  return pages;
}

function updateSummary(reports) { // 상단 통계 계산
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

function renderTodayDetect(reports) { // 오늘 신고 3개 표시
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

function createTodayDetectItem(report) { // 오늘 탐지 기록 카드 생성
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

function createReportCard(report) { // 신고 카드 생성
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

function getStatusClass(status) { // 상태 배지 클래스 반환
  if (status === "접수") return "badge-status-received";
  if (status === "확인중") return "badge-status-checking";
  if (status === "처리완료" || status === "처리 완료") return "badge-status-done";
  if (status === "오탐") return "badge-status-false";
  return "badge-location";
}

function getRiskClass(status) { // 위험도 색상 클래스 반환
  if (status === "처리완료" || status === "처리 완료") return "safe";
  if (status === "확인중") return "warning";
  if (status === "오탐") return "safe";
  return "danger";
}

function getRiskLabel(status) { // 위험도 텍스트 반환
  if (status === "처리완료" || status === "처리 완료") return "저위험";
  if (status === "확인중") return "중위험";
  if (status === "오탐") return "저위험";
  return "고위험";
}

function isToday(createdAt) { // 오늘 날짜인지 확인
  if (!createdAt) return false;

  const dateOnly = createdAt.split(" ")[0];
  const today = new Date();

  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");
  const todayStr = `${yyyy}-${mm}-${dd}`;

  return dateOnly === todayStr;
}

function extractTime(createdAt) { // 시간만 추출
  if (!createdAt) return "-";

  const parts = createdAt.split(" ");
  if (parts.length < 2) return createdAt;

  const timeParts = parts[1].split(":");
  if (timeParts.length >= 2) {
    return `${timeParts[0]}:${timeParts[1]}`;
  }

  return parts[1];
}

function escapeHtml(value) { // HTML 특수문자 이스케이프 처리
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}