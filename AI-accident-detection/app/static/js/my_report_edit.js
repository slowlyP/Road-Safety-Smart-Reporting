document.addEventListener("DOMContentLoaded", function () {

  const previewItem = document.querySelector(".edit-file-preview-item");
  const previewBox = document.getElementById("edit-file-preview");

  const fileInput = document.getElementById("new_file");
  const fileNameText = document.getElementById("edit-file-name");

  if (!previewBox) return;


  /* ===== 기존 파일 보여주기 ===== */
  function showEmptyMessage(message) {

    previewBox.innerHTML = `
      <p class="edit-file-empty-text">
        ${message}
      </p>
    `;
  }

  function renderExistingFile(fileUrl, fileType) {

    if (!fileUrl || !fileType || fileUrl.trim() === "") {
      showEmptyMessage("등록된 파일이 없습니다.");
      return;
    }

    if (fileType === "이미지") {

      previewBox.innerHTML = `
        <div class="edit-file-preview-item">

          <img
            src="${fileUrl}"
            alt="등록된 이미지"
            class="edit-image-file"
          >

        </div>
      `;

    } else if (fileType === "영상") {

      previewBox.innerHTML = `
        <div class="edit-file-preview-item">

          <video
            controls
            class="edit-video-preview"
          >
            <source src="${fileUrl}">
            브라우저가 영상을 지원하지 않습니다.
          </video>

        </div>
      `;

    } else {

      previewBox.innerHTML = `
        <div class="edit-file-preview-item">

          <a
            href="${fileUrl}"
            target="_blank"
            class="edit-file-link"
          >
            파일 보기
          </a>

        </div>
      `;

    }
  }


  if (previewItem) {

    const fileUrl = previewItem.dataset.fileUrl;
    const fileType = previewItem.dataset.fileType;

    renderExistingFile(fileUrl, fileType);

  } else {

    showEmptyMessage("등록된 파일이 없습니다.");

  }


  /* ===== 새 파일 선택 ===== */
  if (fileInput) {

    fileInput.addEventListener("change", function () {

      const file = this.files[0];

      /* 파일명 표시 */
      if (fileNameText) {

        if (file) {
          fileNameText.textContent = file.name;
        } else {
          fileNameText.textContent = "선택된 파일 없음";
        }

      }

      if (!file) return;

      const fileType = file.type;
      const objectUrl = URL.createObjectURL(file);


      /* 미리보기 변경 */
      if (fileType.startsWith("image")) {

        previewBox.innerHTML = `
          <div class="edit-file-preview-item">

            <img
              src="${objectUrl}"
              alt="새 이미지 미리보기"
              class="edit-image-file"
            >

          </div>
        `;

      } else if (fileType.startsWith("video")) {

        previewBox.innerHTML = `
          <div class="edit-file-preview-item">

            <video
              controls
              class="edit-video-preview"
            >
              <source src="${objectUrl}">
              브라우저가 영상을 지원하지 않습니다.
            </video>

          </div>
        `;

      } else {

        showEmptyMessage("미리보기를 지원하지 않는 파일입니다.");

      }

    });

  }

});