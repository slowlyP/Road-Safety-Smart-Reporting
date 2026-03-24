// 문서 로딩이 끝난 뒤 수정 페이지 기능 실행
document.addEventListener("DOMContentLoaded", function () {

  // 기존 파일 미리보기 요소 찾기
  const previewItem = document.querySelector(".edit-file-preview-item");

  // 미리보기 전체 박스 찾기
  const previewBox = document.getElementById("edit-file-preview");

  // 새 파일 입력창 찾기
  const fileInput = document.getElementById("new_file");

  // 선택한 파일명 표시 영역 찾기
  const fileNameText = document.getElementById("edit-file-name");

  // 미리보기 박스가 없으면 스크립트 종료
  if (!previewBox) return;


  /* ===== 기존 파일 보여주기 ===== */

  // 등록된 파일이 없을 때 안내 문구 표시
  function showEmptyMessage(message) {
    previewBox.innerHTML = `
      <p class="edit-file-empty-text">
        ${message}
      </p>
    `;
  }

  // 기존 첨부파일 종류에 따라 미리보기 렌더링
  function renderExistingFile(fileUrl, fileType) {

    // 파일 정보가 없으면 빈 메시지 표시
    if (!fileUrl || !fileType || fileUrl.trim() === "") {
      showEmptyMessage("등록된 파일이 없습니다.");
      return;
    }

    // 기존 파일이 이미지면 이미지 미리보기 출력
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

    // 기존 파일이 영상이면 영상 미리보기 출력
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

    // 이미지/영상이 아니면 파일 링크로 표시
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

  // 기존 첨부파일 데이터가 있으면 미리보기 출력
  if (previewItem) {

    // data 속성에서 파일 경로와 파일 종류 읽기
    const fileUrl = previewItem.dataset.fileUrl;
    const fileType = previewItem.dataset.fileType;

    // 기존 파일 미리보기 렌더링
    renderExistingFile(fileUrl, fileType);

  } else {

    // 기존 첨부파일이 없으면 안내 문구 표시
    showEmptyMessage("등록된 파일이 없습니다.");

  }


  /* ===== 새 파일 선택 ===== */

  // 파일 입력창이 있으면 change 이벤트 연결
  if (fileInput) {

    // 새 파일 선택 시 파일명과 미리보기 갱신
    fileInput.addEventListener("change", function () {

      // 사용자가 새로 선택한 첫 번째 파일 가져오기
      const file = this.files[0];

      /* 파일명 표시 */

      // 파일명 표시 영역이 있으면 텍스트 갱신
      if (fileNameText) {

        // 파일이 있으면 파일명 표시
        if (file) {
          fileNameText.textContent = file.name;
        } else {
          fileNameText.textContent = "선택된 파일 없음";
        }

      }

      // 선택된 파일이 없으면 종료
      if (!file) return;

      // 파일 MIME 타입 가져오기
      const fileType = file.type;

      // 브라우저 미리보기용 임시 URL 생성
      const objectUrl = URL.createObjectURL(file);


      /* 미리보기 변경 */

      // 선택 파일이 이미지면 이미지 미리보기 표시
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

      // 선택 파일이 영상이면 영상 미리보기 표시
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

      // 지원하지 않는 파일이면 안내 문구 표시
      } else {

        showEmptyMessage("미리보기를 지원하지 않는 파일입니다.");

      }

    });

  }

});