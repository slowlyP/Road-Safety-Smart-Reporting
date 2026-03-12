let map;
let marker;
let geocoder;
let autocomplete;

// 1. 구글 지도 초기화 및 설정
function initMap() {
    const initialPos = { lat: 37.5665, lng: 126.9780 };
    geocoder = new google.maps.Geocoder();
    
    map = new google.maps.Map(document.getElementById("map"), {
        center: initialPos,
        zoom: 15,
    });

    marker = new google.maps.Marker({
        position: initialPos,
        map: map,
        draggable: true, // 지도 안의 '마커' 드래그 가능
    });

    google.maps.event.addListener(marker, 'dragend', function() {
        updatePosition(marker.getPosition());
    });

    map.addListener("click", (e) => {
        marker.setPosition(e.latLng);
        updatePosition(e.latLng);
    });

    initAutocomplete();
}

// 2. 주소 자동완성
function initAutocomplete() {
    const input = document.getElementById("location_text");
    autocomplete = new google.maps.places.Autocomplete(input);
    autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.geometry.location) return;
        map.setCenter(place.geometry.location);
        marker.setPosition(place.geometry.location);
        updatePosition(place.geometry.location);
    });
}

function updatePosition(latLng) {
    document.getElementById("latitude").value = latLng.lat();
    document.getElementById("longitude").value = latLng.lng();
    geocoder.geocode({ location: latLng }, (results, status) => {
        if (status === "OK" && results[0]) {
            document.getElementById("location_text").value = results[0].formatted_address;
        }
    });
}

// ---------------------------------------------------------
// 3. [핵심] 팝업(모달)창 마우스 드래그 이동 로직
// ---------------------------------------------------------
const modalContent = document.querySelector('.modal-content');
const modalHeader = document.querySelector('.modal-header');

if (modalHeader && modalContent) {
    let isDragging = false;
    let offset = { x: 0, y: 0 };

    modalHeader.style.cursor = 'move'; // 헤더에 마우스 올리면 이동 커서로 변경

    modalHeader.addEventListener('mousedown', (e) => {
        isDragging = true;
        // 클릭한 지점과 창의 왼쪽 상단 모서리 사이의 거리 계산
        offset.x = e.clientX - modalContent.offsetLeft;
        offset.y = e.clientY - modalContent.offsetTop;
        modalContent.style.margin = '0'; // 중앙 정렬 해제 (이동을 위해)
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        // 마우스 움직임에 따라 창 위치 업데이트
        modalContent.style.position = 'absolute';
        modalContent.style.left = (e.clientX - offset.x) + 'px';
        modalContent.style.top = (e.clientY - offset.y) + 'px';
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });
}

// ---------------------------------------------------------
// 4. 기존 드래그 앤 드롭 업로드 및 제출 로직 (유지)
// ---------------------------------------------------------
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('fileInput');

if (dropZone) {
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#FF6B00';
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = '#2A2A2A';
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            updateFileInfo(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) updateFileInfo(fileInput.files[0]);
    });
}

// 1. [수정] 파일 미리보기 함수 (텍스트 표시에서 이미지/영상 표시로 변경)
function updateFileInfo(file) {
    const infoText = dropZone.querySelector('p');
    const icon = dropZone.querySelector('i');
    const previewContainer = document.getElementById('file-preview');
    
    // 기존 미리보기 내용 삭제
    previewContainer.innerHTML = '';
    
    if (file) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            let previewElement;
            
            // 이미지 파일인 경우
            if (file.type.startsWith('image/')) {
                previewElement = document.createElement('img');
            } 
            // 동영상 파일인 경우
            else if (file.type.startsWith('video/')) {
                previewElement = document.createElement('video');
                previewElement.autoplay = true;
                previewElement.muted = true;
                previewElement.loop = true;
                previewElement.playsInline = true;
            }
            
            if (previewElement) {
                previewElement.src = e.target.result;
                previewElement.classList.add('inner-preview'); // CSS 적용
                previewContainer.appendChild(previewElement);
                
                // UI 전환: 미리보기는 보이고, 기존 문구와 아이콘은 숨김
                previewContainer.style.display = 'flex'; 
                if (infoText) infoText.style.display = 'none';
                if (icon) icon.style.display = 'none';
            }
        };
        
        reader.readAsDataURL(file);
    }
}

// 2. [유지/확인] 신고 제출 로직
const reportForm = document.getElementById('reportForm');
if (reportForm) {
    reportForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(reportForm);
        const firstFile = fileInput.files[0];
        
        if (!firstFile) {
            alert('사진 또는 영상을 첨부해주세요.');
            return;
        }

        // 서버에서 구분하기 쉽게 타입 추가
        const type = firstFile.type.includes('image') ? '이미지' : '영상';
        formData.append('report_type', type);

        try {
            const response = await fetch('/api/report', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();

            if (response.ok) {
                alert('신고가 성공적으로 접수되었습니다!');
                window.location.href = '/'; 
            } else {
                alert(result.error || '전송 중 오류가 발생했습니다.');
            }
        } catch (error) {
            console.error('네트워크 오류:', error);
            alert('서버 연결 실패');
        }
    });
}

// URL 또는 파일 데이터를 받아 미리보기를 띄우는 통합 함수
function showPreview(source, isVideo = false) {
    const infoText = dropZone.querySelector('p');
    const icon = dropZone.querySelector('i');
    const previewContainer = document.getElementById('file-preview');
    
    previewContainer.innerHTML = ''; // 초기화

    let previewElement;
    if (isVideo) {
        previewElement = document.createElement('video');
        previewElement.autoplay = true;
        previewElement.muted = true;
        previewElement.loop = true;
    } else {
        previewElement = document.createElement('img');
    }

    previewElement.src = source; // 파일 데이터(base64)나 일반 URL(http) 모두 가능
    previewElement.classList.add('inner-preview');
    
    previewContainer.appendChild(previewElement);
    previewContainer.style.display = 'flex';
    
    if (infoText) infoText.style.display = 'none';
    if (icon) icon.style.display = 'none';
}

// 예: 만약 주소 입력창에 이미지 URL을 붙여넣었을 때 바로 보여주고 싶다면?
document.getElementById('location_text').addEventListener('input', (e) => {
    const value = e.target.value;
    // 입력값이 http로 시작하고 이미지 확장자라면 미리보기 실행
    if (value.startsWith('http') && (value.match(/\.(jpeg|jpg|gif|png)$/) != null)) {
        showPreview(value, false);
    }
});

// 모달 열기/닫기
function openMapModal() {
    document.getElementById("mapModal").style.display = "flex";
    setTimeout(() => {
        google.maps.event.trigger(map, "resize");
        map.setCenter(marker.getPosition());
    }, 100);
}

function closeMapModal() {
    document.getElementById("mapModal").style.display = "none";
}

function confirmLocation() {
    closeMapModal();
}

// 현재 위치 가져오기 기능 추가
function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const pos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                };

                // 1. 지도의 중심을 현재 위치로 이동
                map.setCenter(pos);
                map.setZoom(17); // 조금 더 가깝게 줌인

                // 2. 마커 위치 변경
                marker.setPosition(pos);

                // 3. 위도, 경도 정보 업데이트 (기존 updatePosition 함수 활용)
                updatePosition(pos);
                
                console.log("현재 위치를 찾았습니다.");
            },
            () => {
                alert("현재 위치를 가져오는데 실패했습니다. 위치 권한을 확인해주세요.");
            }
        );
    } else {
        alert("이 브라우저에서는 위치 정보를 사용할 수 없습니다.");
    }
}