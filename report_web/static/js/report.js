// [파일 위치: report_web/static/js/report.js]

// 1. 요소 가져오기 (HTML의 ID와 정확히 일치시킴)
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('fileInput');
const locationBtn = document.getElementById('getLocationBtn');
const reportForm = document.getElementById('reportForm');

// ---------------------------------------------------------
// 2. 위치 수집 로직
// ---------------------------------------------------------
if (locationBtn) {
    locationBtn.addEventListener('click', () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                document.getElementById('latitude').value = lat;
                document.getElementById('longitude').value = lng;
                document.getElementById('location_text').value = `위도: ${lat.toFixed(4)}, 경도: ${lng.toFixed(4)}`;
                alert('현재 위치 정보가 수집되었습니다.');
            }, () => {
                alert('위치 정보를 가져올 수 없습니다. GPS 설정을 확인해주세요.');
            });
        } else {
            alert('이 브라우저는 위치 서비스를 지원하지 않습니다.');
        }
    });
}

// ---------------------------------------------------------
// 3. 드래그 앤 드롭 및 클릭 업로드
// ---------------------------------------------------------

// 영역 클릭 시 파일 창 열기
dropZone.addEventListener('click', () => fileInput.click());

// 드래그 디자인 효과
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('active'); // CSS에 .active 스타일이 있다면 활용
    dropZone.style.borderColor = '#007bff';
    dropZone.style.backgroundColor = '#f0f8ff';
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('active');
    dropZone.style.borderColor = '#ccc';
    dropZone.style.backgroundColor = 'transparent';
});

// 파일 드롭 시 처리
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '#ccc';
    dropZone.style.backgroundColor = 'transparent';

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files; // 드롭된 파일을 input에 수동 할당
        updateFileInfo(files[0]);
    }
});

// 파일 선택창에서 선택 시 처리
fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        updateFileInfo(fileInput.files[0]);
    }
});

// 파일명 표시 함수
function updateFileInfo(file) {
    const infoText = dropZone.querySelector('p');
    infoText.innerText = `선택됨: ${file.name}`;
    infoText.style.color = '#007bff';
}

// ---------------------------------------------------------
// 4. 신고 제출 (백엔드 전송)
// ---------------------------------------------------------
reportForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(reportForm);
    
    const firstFile = fileInput.files[0];
    if (firstFile) {
        const type = firstFile.type.includes('image') ? '이미지' : '영상';
        formData.append('report_type', type);
    } else {
        alert('사진 또는 영상을 첨부해주세요.');
        return;
    }

    try {
        const response = await fetch('/api/report', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();

        if (response.ok) {
            alert(result.message || '신고가 성공적으로 접수되었습니다!');
            window.location.href = '/'; 
        } else {
            alert(result.error || '전송 중 오류가 발생했습니다.');
        }
    } catch (error) {
        console.error('네트워크 오류:', error);
        alert('서버에 연결할 수 없습니다.');
    }
});