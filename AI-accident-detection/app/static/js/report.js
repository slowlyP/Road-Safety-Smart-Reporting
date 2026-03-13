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
        draggable: true,
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

// [통합] 위경도 및 주소 업데이트 함수
function updatePosition(latLng) {
    const lat = typeof latLng.lat === 'function' ? latLng.lat() : latLng.lat;
    const lng = typeof latLng.lng === 'function' ? latLng.lng() : latLng.lng;

    document.getElementById("latitude").value = lat;
    document.getElementById("longitude").value = lng;

    const locationObj = { lat: parseFloat(lat), lng: parseFloat(lng) };

    geocoder.geocode({ location: locationObj }, (results, status) => {
        if (status === "OK" && results[0]) {
            const address = results[0].formatted_address;
            const locationInput = document.getElementById("location_text");
            if (locationInput) {
                locationInput.value = address;
            }
        } else if (status === "REQUEST_DENIED") {
            console.error("Geocoding API 권한을 확인하세요.");
        }
    });
}

// ---------------------------------------------------------
// 3. 팝업(모달)창 드래그 이동 로직
// ---------------------------------------------------------
const modalContent = document.querySelector('.modal-content');
const modalHeader = document.querySelector('.modal-header');

if (modalHeader && modalContent) {
    let isDragging = false;
    let offset = { x: 0, y: 0 };

    modalHeader.style.cursor = 'move';

    modalHeader.addEventListener('mousedown', (e) => {
        isDragging = true;
        offset.x = e.clientX - modalContent.offsetLeft;
        offset.y = e.clientY - modalContent.offsetTop;
        modalContent.style.margin = '0';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        modalContent.style.position = 'absolute';
        modalContent.style.left = (e.clientX - offset.x) + 'px';
        modalContent.style.top = (e.clientY - offset.y) + 'px';
    });

    document.addEventListener('mouseup', () => { isDragging = false; });
}

// ---------------------------------------------------------
// 4. 드래그 앤 드롭 업로드 (일반 파일 및 기본 URL 지원)
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
        dropZone.style.borderColor = '#2A2A2A';

        // 1. 파일이 드롭된 경우
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            updateFileInfo(e.dataTransfer.files[0]);
        } 
        // 2. 텍스트(URL)가 드롭된 경우
        else {
            const droppedUrl = e.dataTransfer.getData('url') || 
                               e.dataTransfer.getData('text/uri-list') || 
                               e.dataTransfer.getData('text');

            const cleanUrl = droppedUrl ? droppedUrl.trim() : "";

            if (cleanUrl.startsWith('http')) {
                const urlInput = document.getElementById('video_url_direct');
                if (urlInput) urlInput.value = cleanUrl;
                
                // 순수 확장자로만 비디오 판별
                const isVideo = /\.(mp4|webm|ogg|mov)/i.test(cleanUrl);
                updateFileInfo(cleanUrl, isVideo);
            }
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) updateFileInfo(fileInput.files[0]);
    });
}

// ---------------------------------------------------------
// 5. 신고 제출 로직
// ---------------------------------------------------------
const reportForm = document.getElementById('reportForm');
if (reportForm) {
    reportForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(reportForm);
        const firstFile = fileInput.files[0];
        const videoUrl = document.getElementById('video_url_direct')?.value;

        if (!firstFile && !videoUrl) {
            alert('사진/영상 파일 또는 URL 주소를 첨부해주세요.');
            return;
        }

        let type = '이미지';
        if (firstFile) {
            type = firstFile.type.includes('image') ? '이미지' : '영상';
        } else if (videoUrl) {
            type = '영상';
            formData.append('video_url', videoUrl);
        }
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
                alert(result.error || '전송 오류 발생');
            }
        } catch (error) {
            alert('서버 연결 실패');
        }
    });
}

// ---------------------------------------------------------
// 6. 미리보기 함수 (일반 사진/영상 전용)
// ---------------------------------------------------------
function updateFileInfo(source, isVideo = false) {
    const previewContainer = document.getElementById('file-preview');
    const infoText = dropZone.querySelector('p');
    const icon = dropZone.querySelector('i');
    
    previewContainer.innerHTML = ''; // 초기화

    // 1. 소스가 파일 객체인 경우
    if (source instanceof File) {
        const reader = new FileReader();
        reader.onload = (e) => renderPreview(e.target.result, source.type.startsWith('video/'));
        reader.readAsDataURL(source);
    } 
    // 2. 소스가 URL 문자열인 경우
    else {
        renderPreview(source, isVideo);
    }

    // 화면에 태그를 그려주는 내부 함수
    function renderPreview(src, isVid) {
        let el = isVid ? document.createElement('video') : document.createElement('img');
        
        if (isVid) {
            el.autoplay = true;
            el.muted = true;
            el.controls = true;
        }
        el.src = src;
        
        el.classList.add('inner-preview');
        previewContainer.appendChild(el);
        
        previewContainer.style.display = 'flex';
        if (infoText) infoText.style.display = 'none';
        if (icon) icon.style.display = 'none';
    }
}

// ---------------------------------------------------------
// 7. 모달창 및 현재 위치 가져오기 관련 함수들
// ---------------------------------------------------------
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

function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            const pos = { lat: position.coords.latitude, lng: position.coords.longitude };
            map.setCenter(pos);
            map.setZoom(17);
            marker.setPosition(pos);
            updatePosition(pos);
        });
    } else {
        alert("이 브라우저에서는 위치 정보를 사용할 수 없습니다.");
    }
}