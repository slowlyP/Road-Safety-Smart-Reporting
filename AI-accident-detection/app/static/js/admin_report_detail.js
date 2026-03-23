document.addEventListener("DOMContentLoaded", () => {
  const analysisEl = document.getElementById("ai-analysis-data");
  if (!analysisEl) return;

  const aiAnalysis = JSON.parse(analysisEl.textContent || "[]");

  renderAiSummary(aiAnalysis);
  renderAiHistory(aiAnalysis);
  initMediaCanvas(aiAnalysis);
});

function renderAiSummary(aiAnalysis) {
  const summaryBox = document.getElementById("ai-summary-box");
  if (!summaryBox) return;

  if (!aiAnalysis.length) {
    summaryBox.innerHTML = '<div class="empty-box">탐지 결과가 없습니다.</div>';
    return;
  }

  const counts = {};
  aiAnalysis.forEach(item => {
    const key = item.label_kor || item.detected_label || "기타";
    counts[key] = (counts[key] || 0) + 1;
  });

  const html = Object.entries(counts)
    .map(([label, count]) => {
      return `
        <div class="summary-item">
          <span class="summary-label">${label}</span>
          <strong class="summary-count">${count}건</strong>
        </div>
      `;
    })
    .join("");

  summaryBox.innerHTML = html;
}

function renderAiHistory(aiAnalysis) {
  const historyBox = document.getElementById("ai-history-box");
  if (!historyBox) return;

  if (!aiAnalysis.length) {
    historyBox.innerHTML = '<div class="empty-box">분석 이력이 없습니다.</div>';
    return;
  }

  const sorted = [...aiAnalysis].sort((a, b) => {
    const t1 = a.time_sec ?? -1;
    const t2 = b.time_sec ?? -1;
    if (t1 !== t2) return t1 - t2;
    return (a.id || 0) - (b.id || 0);
  });

  historyBox.innerHTML = sorted.map(item => {
    const timeText = item.time_sec != null ? `${item.time_sec.toFixed(2)}초` : "이미지";
    const confText = item.confidence != null ? `${(item.confidence * 100).toFixed(1)}%` : "-";

    return `
      <div class="history-item">
        <div class="history-main">
          <strong>${item.label_kor || item.detected_label}</strong>
        </div>
        <div class="history-sub">
          시간: ${timeText} / 정확도: ${confText}
        </div>
      </div>
    `;
  }).join("");
}

function initMediaCanvas(aiAnalysis) {
  const wrappers = document.querySelectorAll(".media-wrapper");

  wrappers.forEach(wrapper => {
    const fileId = Number(wrapper.dataset.fileId);
    const canvas = wrapper.querySelector("canvas");
    const image = wrapper.querySelector("img");
    const video = wrapper.querySelector("video");

    if (!canvas) return;

    const detections = aiAnalysis.filter(item => Number(item.file_id) === fileId);

    if (image) {
      image.addEventListener("load", () => {
        syncCanvasSize(canvas, image);
        drawImageDetections(canvas, image, detections);
      });

      if (image.complete) {
        syncCanvasSize(canvas, image);
        drawImageDetections(canvas, image, detections);
      }
    }

    if (video) {
      const renderVideo = () => {
        syncCanvasSize(canvas, video);
        drawVideoDetections(canvas, video, detections);
      };

      video.addEventListener("loadedmetadata", renderVideo);
      video.addEventListener("loadeddata", renderVideo);
      video.addEventListener("timeupdate", renderVideo);
      video.addEventListener("seeked", renderVideo);
      video.addEventListener("pause", renderVideo);
      video.addEventListener("play", renderVideo);
      window.addEventListener("resize", renderVideo);
    }
  });
}

function syncCanvasSize(canvas, mediaEl) {
  const rect = mediaEl.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
}

function drawImageDetections(canvas, image, detections) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  detections.forEach(item => {
    drawBox(ctx, canvas, {
      bbox: item.bbox,
      label: item.label_kor || item.detected_label,
      confidence: item.confidence,
      sourceWidth: image.naturalWidth || canvas.width,
      sourceHeight: image.naturalHeight || canvas.height
    });
  });
}

function drawVideoDetections(canvas, video, detections) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const currentTime = video.currentTime || 0;

  const visible = detections.filter(item => {
    if (item.time_sec == null) return false;
    return Math.abs(item.time_sec - currentTime) <= 0.20;
  });

  visible.forEach(item => {
    drawBox(ctx, canvas, {
      bbox: item.bbox,
      label: item.label_kor || item.detected_label,
      confidence: item.confidence,
      sourceWidth: item.frame_width || video.videoWidth || canvas.width,
      sourceHeight: item.frame_height || video.videoHeight || canvas.height
    });
  });
}

function drawBox(ctx, canvas, { bbox, label, confidence, sourceWidth, sourceHeight }) {
  if (!bbox || bbox.length !== 4 || !sourceWidth || !sourceHeight) return;

  const scaleX = canvas.width / sourceWidth;
  const scaleY = canvas.height / sourceHeight;

  const x1 = bbox[0] * scaleX;
  const y1 = bbox[1] * scaleY;
  const x2 = bbox[2] * scaleX;
  const y2 = bbox[3] * scaleY;

  const boxW = x2 - x1;
  const boxH = y2 - y1;

  ctx.lineWidth = 2;
  ctx.strokeStyle = "#ff3b30";
  ctx.strokeRect(x1, y1, boxW, boxH);

  const confText = confidence != null ? ` ${(confidence * 100).toFixed(1)}%` : "";
  const text = `${label}${confText}`;

  ctx.font = "14px Arial";
  const textWidth = ctx.measureText(text).width;
  const textHeight = 20;

  ctx.fillStyle = "#ff3b30";
  ctx.fillRect(x1, Math.max(0, y1 - textHeight), textWidth + 12, textHeight);

  ctx.fillStyle = "#ffffff";
  ctx.fillText(text, x1 + 6, Math.max(14, y1 - 6));
}