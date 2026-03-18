document.addEventListener("DOMContentLoaded", () => {
  const dataElement = document.getElementById("ai-analysis-data");
  const detections = dataElement ? JSON.parse(dataElement.textContent) : [];

  const CLASS_COLOR_MAP = {
    "falling_object": "#ff3b30",
    "box": "#007aff",
    "tire": "#ff9500",
    "metal": "#af52de",
    "unknown": "#34c759"
  };

  const LABEL_KOR_MAP = {
    "falling_object": "낙하물",
    "box": "박스",
    "tire": "타이어",
    "metal": "금속",
    "unknown": "기타"
  };

  function getColorByLabel(label) {
    return CLASS_COLOR_MAP[label] || "#ffffff";
  }

  function getLabelName(det) {
    return det.label_kor || LABEL_KOR_MAP[det.detected_label] || det.detected_label || "객체";
  }

  const groupedByFileId = {};
  detections.forEach(det => {
    const fileId = String(det.file_id);
    if (!groupedByFileId[fileId]) {
      groupedByFileId[fileId] = [];
    }
    groupedByFileId[fileId].push(det);
  });

  function getDisplayRect(mediaEl, naturalWidth, naturalHeight) {
    const containerWidth = mediaEl.clientWidth;
    const containerHeight = mediaEl.clientHeight;

    if (!containerWidth || !containerHeight || !naturalWidth || !naturalHeight) {
      return null;
    }

    const mediaRatio = naturalWidth / naturalHeight;
    const containerRatio = containerWidth / containerHeight;

    let drawWidth, drawHeight, offsetX, offsetY;

    if (mediaRatio > containerRatio) {
      drawWidth = containerWidth;
      drawHeight = containerWidth / mediaRatio;
      offsetX = 0;
      offsetY = (containerHeight - drawHeight) / 2;
    } else {
      drawHeight = containerHeight;
      drawWidth = containerHeight * mediaRatio;
      offsetY = 0;
      offsetX = (containerWidth - drawWidth) / 2;
    }

    return { drawWidth, drawHeight, offsetX, offsetY };
  }

  function drawDetections(canvas, mediaEl, detectionList, naturalWidth, naturalHeight) {
    if (!canvas || !mediaEl || !detectionList || !detectionList.length) return;
    if (!naturalWidth || !naturalHeight) return;

    const ctx = canvas.getContext("2d");
    const canvasWidth = mediaEl.clientWidth;
    const canvasHeight = mediaEl.clientHeight;

    if (!canvasWidth || !canvasHeight) return;

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const rect = getDisplayRect(mediaEl, naturalWidth, naturalHeight);
    if (!rect) return;

    const scaleX = rect.drawWidth / naturalWidth;
    const scaleY = rect.drawHeight / naturalHeight;

    detectionList.forEach(det => {
      const x1 = rect.offsetX + (det.bbox[0] * scaleX);
      const y1 = rect.offsetY + (det.bbox[1] * scaleY);
      const x2 = rect.offsetX + (det.bbox[2] * scaleX);
      const y2 = rect.offsetY + (det.bbox[3] * scaleY);

      const boxWidth = x2 - x1;
      const boxHeight = y2 - y1;

      const labelName = getLabelName(det);
      const confidence = Number(det.confidence || 0).toFixed(2);
      const labelText = `${labelName} (${confidence})`;

      const color = getColorByLabel(det.detected_label);

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(x1, y1, boxWidth, boxHeight);

      ctx.font = "bold 14px Arial";
      const textWidth = ctx.measureText(labelText).width;
      const labelBoxHeight = 22;
      const labelX = x1;
      const labelY = Math.max(y1 - labelBoxHeight, 0);

      ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
      ctx.fillRect(labelX, labelY, textWidth + 12, labelBoxHeight);

      ctx.strokeStyle = "#000000";
      ctx.lineWidth = 3;
      ctx.strokeText(labelText, labelX + 6, labelY + 15);

      ctx.fillStyle = "#ffffff";
      ctx.fillText(labelText, labelX + 6, labelY + 15);
    });
  }

  function setupImage(fileId, detectionList) {
    const image = document.getElementById(`image-${fileId}`);
    const canvas = document.getElementById(`canvas-${fileId}`);

    if (!image || !canvas) return;

    const render = () => {
      drawDetections(
        canvas,
        image,
        detectionList,
        image.naturalWidth,
        image.naturalHeight
      );
    };

    if (image.complete) {
      render();
    } else {
      image.addEventListener("load", render);
    }

    window.addEventListener("resize", render);
  }

  function setupVideo(fileId, detectionList) {
    const video = document.getElementById(`video-${fileId}`);
    const canvas = document.getElementById(`canvas-${fileId}`);

    if (!video || !canvas) return;

    const render = () => {
      drawDetections(
        canvas,
        video,
        detectionList,
        video.videoWidth,
        video.videoHeight
      );
    };

    video.addEventListener("loadedmetadata", render);
    video.addEventListener("loadeddata", render);
    video.addEventListener("play", render);
    video.addEventListener("pause", render);
    window.addEventListener("resize", render);
  }

  function summarizeDetections(list) {
    const summary = {};

    list.forEach(det => {
      const label = det.detected_label || "unknown";

      if (!summary[label]) {
        summary[label] = {
          label,
          labelKor: getLabelName(det),
          count: 0,
          totalConfidence: 0,
          maxConfidence: 0
        };
      }

      const confidence = Number(det.confidence || 0);

      summary[label].count += 1;
      summary[label].totalConfidence += confidence;
      summary[label].maxConfidence = Math.max(summary[label].maxConfidence, confidence);
    });

    Object.values(summary).forEach(item => {
      item.avgConfidence = item.count ? item.totalConfidence / item.count : 0;
    });

    return Object.values(summary).sort((a, b) => {
      if (b.count !== a.count) return b.count - a.count;
      return b.avgConfidence - a.avgConfidence;
    });
  }

  function renderSummary(summaryList) {
    const container = document.getElementById("ai-summary-box");
    if (!container) return;

    if (!summaryList.length) {
      container.innerHTML = `<div class="empty-box">요약할 탐지 데이터가 없습니다.</div>`;
      return;
    }

    const maxCount = Math.max(...summaryList.map(item => item.count));
    const finalResult = summaryList[0];

    let html = "";

    summaryList.forEach(item => {
      const color = getColorByLabel(item.label);
      const barWidth = maxCount ? (item.count / maxCount) * 100 : 0;

      html += `
        <div class="summary-item">
          <div class="summary-label-row">
            <span class="summary-label" style="color:${color}">
              ${item.labelKor} (${item.label})
            </span>
            <span class="summary-count">${item.count}회 탐지</span>
          </div>

          <div class="summary-bar-track">
            <div class="summary-bar-fill" style="width:${barWidth}%; background:${color};"></div>
          </div>

          <div class="summary-meta">
            <span>평균 신뢰도 ${item.avgConfidence.toFixed(2)}</span>
            <span>최대 신뢰도 ${item.maxConfidence.toFixed(2)}</span>
          </div>
        </div>
      `;
    });

    html += `
      <div class="summary-result-box">
        <div class="summary-result-title">최종 판단</div>
        <div class="summary-result-value" style="color:${getColorByLabel(finalResult.label)}">
          ${finalResult.labelKor} (${finalResult.label})
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  function renderHistory(list) {
    const container = document.getElementById("ai-history-box");
    if (!container) return;

    if (!list.length) {
      container.innerHTML = `<div class="empty-box">AI 분석 결과가 아직 없습니다.</div>`;
      return;
    }

    const sortedList = [...list].sort((a, b) => {
      const aTime = a.detected_at || "";
      const bTime = b.detected_at || "";
      return bTime.localeCompare(aTime);
    });

    let html = "";

    sortedList.forEach(det => {
      const labelName = getLabelName(det);
      const color = getColorByLabel(det.detected_label);

      html += `
        <div class="history-item">
          <div class="history-main">
            탐지 객체:
            <strong style="color:${color}">${labelName}</strong>
            (${det.detected_label || "unknown"})
          </div>
          <div class="history-sub">
            신뢰도: ${Number(det.confidence || 0).toFixed(2)} /
            파일 ID: ${det.file_id ?? "-"} /
            탐지 시각: ${det.detected_at || "-"}
          </div>
          <div class="history-sub">
            BBox: ${det.bbox?.[0] ?? "-"}, ${det.bbox?.[1] ?? "-"}, ${det.bbox?.[2] ?? "-"}, ${det.bbox?.[3] ?? "-"}
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  }

  Object.keys(groupedByFileId).forEach(fileId => {
    const detectionList = groupedByFileId[fileId];
    setupImage(fileId, detectionList);
    setupVideo(fileId, detectionList);
  });

  const summaryList = summarizeDetections(detections);
  renderSummary(summaryList);
  renderHistory(detections);
});