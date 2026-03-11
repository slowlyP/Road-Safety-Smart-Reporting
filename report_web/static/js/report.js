// [파일 위치: report_web/static/js/report.js]

// 1. 위치 수집 로직 (reports 테이블의 latitude, longitude 매핑)
document.getElementById('getLocationBtn').addEventListener('click', () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            // hidden input에 값 설정
            document.getElementById('latitude').value = lat;
            document.getElementById('longitude').value = lng;
            
            // 화면 표시용 텍스트 설정
            document.getElementById('location_text').value = `위도: ${lat.toFixed(4)}, 경도: ${lng.toFixed(4)}`;
            alert('현재 위치 정보가 수집되었습니다.');
        }, () => {
            alert('위치 정보를 가져올 수 없습니다. GPS 설정을 확인해주세요.');
        });
    } else {
        alert('이 브라우저는 위치 서비스를 지원하지 않습니다.');
    }
});

// 2. 파일 업로드 UI 로직
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('fileInput');

// 구역 클릭 시 파일 선택창 호출
dropZone.addEventListener('click', () => fileInput.click());

// 3. 신고 제출 로직 (Flask 서버와 통신)
document.getElementById('reportForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    
    // 파일이 있으면 이미지/영상 구분하여 report_type 추가 (DB 필드 매핑용)
    const firstFile = fileInput.files[0];
    if (firstFile) {
        const type = firstFile.type.includes('image') ? '이미지' : '영상';
        formData.append('report_type', type);
    }

    try {
        // 백엔드 API 엔드포인트 호출
        const response = await fetch('/api/report', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            alert('신고가 성공적으로 접수되었습니다! AI 분석이 시작됩니다.');
            window.location.href = '/'; // 완료 후 메인 페이지로 이동
        } else {
            alert('서버 전송 중 오류가 발생했습니다.');
        }
    } catch (error) {
        console.error('네트워크 오류:', error);
        alert('서버에 연결할 수 없습니다.');
    }
});