document.addEventListener("DOMContentLoaded", function () {
  const item = document.querySelector(".file-preview-item");
  const previewBox = document.getElementById("detail-image-preview");

  if (!item || !previewBox) return;

  const fileUrl = item.dataset.fileUrl;
  const fileType = item.dataset.fileType;

  if (!fileUrl || !fileType || fileUrl.trim() === "") {
    previewBox.innerHTML = '<p class="image-empty-text">등록된 파일이 없습니다.</p>';
    return;
  }

  if (fileType === "이미지") {
    item.innerHTML = `
      <img src="${fileUrl}" alt="신고 이미지" id="preview-image" class="detail-image-file">
    `;
  } else if (fileType === "영상") {
    item.innerHTML = `
      <video controls id="preview-video" class="detail-video-preview">
        <source src="${fileUrl}">
        브라우저가 영상을 지원하지 않습니다.
      </video>
    `;
  } else {
    item.innerHTML = `
      <a href="${fileUrl}" target="_blank" class="file-download-link">파일 보기</a>
    `;
  }
});