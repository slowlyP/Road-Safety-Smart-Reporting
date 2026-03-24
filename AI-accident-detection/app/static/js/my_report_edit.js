document.addEventListener("DOMContentLoaded", function () {
  /* ===== 기본 요소 ===== */
  const previewBox = document.getElementById("edit-file-preview");
  const fileInput = document.getElementById("new_file");
  const fileNameText = document.getElementById("edit-file-name");
  const deleteFileBtn = document.getElementById("delete-existing-file-btn");
  const deleteFileInput = document.getElementById("delete_file"); // hidden input
  const previewItem = document.querySelector(".edit-file-preview-item");
  const uploadBtn = document.querySelector(".edit-file-upload-btn"); // 버튼 미리 선언

  if (!previewBox) return;

  /* ===== 공통 함수 ===== */
  function showEmptyMessage(message) {
      previewBox.innerHTML = `<p class="edit-empty-file">${message}</p>`;
  }

  function renderExistingFile(fileUrl, fileType) {
      if (!fileUrl || !fileType || fileUrl.trim() === "") {
          showEmptyMessage("등록된 파일이 없습니다.");
          return;
      }

      if (fileType === "이미지") {
          previewBox.innerHTML = `
              <div class="edit-file-preview-item">
                  <img src="${fileUrl}" class="edit-image-file">
              </div>`;
      } else if (fileType === "영상") {
          previewBox.innerHTML = `
              <div class="edit-file-preview-item">
                  <video controls class="edit-video-preview">
                      <source src="${fileUrl}">
                      브라우저가 영상을 지원하지 않습니다.
                  </video>
              </div>`;
      } else {
          previewBox.innerHTML = `
              <div class="edit-file-preview-item">
                  <a href="${fileUrl}" target="_blank" class="edit-file-link">파일 보기</a>
              </div>`;
      }
  }

  /* ===== 1. 기존 파일 초기 렌더링 ===== */
  if (previewItem) {
      const fileUrl = previewItem.dataset.fileUrl;
      const fileType = previewItem.dataset.fileType;
      renderExistingFile(fileUrl, fileType);
  } else {
      showEmptyMessage("등록된 파일이 없습니다.");
  }

  /* ===== 2. 입력 상태 강제 초기화 ===== */
  if (fileInput) {
      fileInput.disabled = false;
      const label = document.querySelector('label[for="new_file"]');
      if (label) label.classList.remove("disabled");
  }

  if (deleteFileBtn) {
      deleteFileBtn.disabled = false;
  }

  /* ===== 3. 기존 파일 삭제 버튼 ===== */
  if (deleteFileBtn && deleteFileInput) {
      deleteFileBtn.addEventListener("click", function () {
          const confirmDelete = confirm("기존 파일을 삭제하시겠습니까? (저장 시 반영됩니다)");
          if (!confirmDelete) return;

          deleteFileInput.value = "Y";
          showEmptyMessage("파일이 삭제되었습니다. 새 파일을 선택해주세요.");
          this.style.display = "none";

          if (fileInput) fileInput.value = "";
          if (fileNameText) fileNameText.textContent = "선택된 파일 없음";
      });
  }

  /* ===== 4. 새 파일 선택 (검증 로직 포함) ===== */
  if (fileInput) {
      fileInput.addEventListener("change", function () {
          const file = this.files[0];

          if (!file) {
              if (fileNameText) fileNameText.textContent = "선택된 파일 없음";
              showEmptyMessage("선택된 파일이 없습니다.");
              return;
          }

          // 1. 용량 제한 체크 (50MB)
          const maxSize = 50 * 1024 * 1024;
          if (file.size > maxSize) {
              alert("파일 용량이 너무 큽니다. 50MB 이하의 파일만 업로드 가능합니다.");
              this.value = ""; 
              if (fileNameText) fileNameText.textContent = "선택된 파일 없음";
              showEmptyMessage("용량 초과로 선택이 취소되었습니다.");
              return;
          }

          if (deleteFileInput) deleteFileInput.value = "N";

          const fileType = file.type;
          const objectUrl = URL.createObjectURL(file);

          if (fileType.startsWith("image")) {
              if (fileNameText) fileNameText.textContent = file.name;
              previewBox.innerHTML = `
                  <div class="edit-file-preview-item">
                      <img src="${objectUrl}" class="edit-image-file">
                  </div>`;
          } else if (fileType.startsWith("video")) {
              const video = document.createElement('video');
              video.preload = 'metadata';

              video.onloadedmetadata = function() {
                  const duration = video.duration;
                  if (duration > 30) {
                      alert(`영상 길이가 30초를 초과합니다. (현재: ${Math.round(duration)}초)\n30초 이내의 영상만 업로드해주세요.`);
                      fileInput.value = ""; 
                      if (fileNameText) fileNameText.textContent = "선택된 파일 없음";
                      showEmptyMessage("영상 길이 제한으로 선택이 취소되었습니다.");
                      URL.revokeObjectURL(objectUrl);
                  } else {
                      if (fileNameText) fileNameText.textContent = file.name;
                      previewBox.innerHTML = `
                          <div class="edit-file-preview-item">
                              <video controls class="edit-video-preview">
                                  <source src="${objectUrl}">
                              </video>
                          </div>`;
                  }
              };
              video.src = objectUrl;
          } else {
              if (fileNameText) fileNameText.textContent = file.name;
              showEmptyMessage("미리보기를 지원하지 않는 파일입니다.");
          }
      });
  }

  /* ===== 5. 파일 업로드 버튼 클릭 이벤트 (버튼 클릭 시 input 연동) ===== */
  if (uploadBtn && fileInput) {
      uploadBtn.addEventListener("click", function (e) {
          e.preventDefault();
          fileInput.click();
      });
  }
}); // <--- 여기서 DOMContentLoaded 중괄호를 확실히 닫아줍니다.