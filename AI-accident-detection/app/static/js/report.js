let map;
let marker;
let geocoder;
let autocomplete;

// 서울 시청 초기 좌표 (사용자가 위치를 변경했는지 확인하기 위한 용도)
const INITIAL_LAT = 37.5665;
const INITIAL_LNG = 126.9780;

// [설정 상수로 관리]
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const MAX_VIDEO_DURATION = 30; // 30초 제한
const ALLOWED_TYPES = [
    'image/jpeg', 'image/png', 'image/webp', 
    'video/mp4', 'video/quicktime', 'video/x-msvideo'
];

// 1. 구글 지도 및 검색(Autocomplete) 초기화
function initMap() {
    const initialPos = { lat: INITIAL_LAT, lng: INITIAL_LNG }; 
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

    initAutocomplete();

    google.maps.event.addListener(marker, 'dragend', function() {
        updatePosition(marker.getPosition());
    });

    map.addListener("click", (e) => {
        marker.setPosition(e.latLng);
        updatePosition(e.latLng);
    });
}

// 2. 주소 검색(자동완성) 기능
function initAutocomplete() {
    const input = document.getElementById("location_text");
    autocomplete = new google.maps.places.Autocomplete(input);
    
    autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.geometry.location) return;

        map.setCenter(place.geometry.location);
        map.setZoom(17);
        marker.setPosition(place.geometry.location);
        
        document.getElementById("latitude").value = place.geometry.location.lat();
        document.getElementById("longitude").value = place.geometry.location.lng();
    });
}

// 3. 좌표 및 주소 텍스트 업데이트
function updatePosition(latLng) {
    if (!latLng) return;

    document.getElementById("latitude").value = latLng.lat();
    document.getElementById("longitude").value = latLng.lng();

    geocoder.geocode({ location: latLng }, (results, status) => {
        if (status === "OK" && results && results[0]) {
            document.getElementById("location_text").value = results[0].formatted_address;
        } else {
            console.error("주소 변환 실패:", status);
            document.getElementById("location_text").value = "주소를 불러오지 못했습니다.";
        }
    });
}

// 4. 모달 제어
function openMapModal() {
    document.getElementById("mapModal").style.display = "flex";
    setTimeout(() => {
        google.maps.event.trigger(map, "resize");
        if (marker) map.setCenter(marker.getPosition());
    }, 100);
}

function closeMapModal() {
    document.getElementById("mapModal").style.display = "none";
}

function confirmLocation() {
    if (!marker) {
        alert("위치를 먼저 선택하세요.");
        return;
    }

    const position = marker.getPosition();
    updatePosition(position);   // 현재 마커 위치를 주소/좌표로 다시 반영
    closeMapModal();
}

// 5. 내 현재 위치 찾기
function getCurrentLocation() {
    if (!navigator.geolocation) {
        alert("이 브라우저에서는 현재 위치 기능을 지원하지 않습니다.");
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const pos = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };

            map.setCenter(pos);
            map.setZoom(17);
            marker.setPosition(pos);
            updatePosition(new google.maps.LatLng(pos.lat, pos.lng));
        },
        (error) => {
            console.error("현재 위치 가져오기 실패:", error);

            let message = "현재 위치를 가져올 수 없습니다.";
            if (error.code === 1) {
                message = "위치 권한이 차단되었습니다. 브라우저에서 위치 권한을 허용해주세요.";
            } else if (error.code === 2) {
                message = "현재 위치를 확인할 수 없습니다.";
            } else if (error.code === 3) {
                message = "위치 요청 시간이 초과되었습니다.";
            }

            alert(message);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

// ---------------------------------------------------------
// 6. 파일 업로드 및 검증 로직 (30초 & 50MB 제한 적용)
// ---------------------------------------------------------
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('fileInput');

if (dropZone) {
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = '#FF6B00'; });
    dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = '#2A2A2A'; });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#2A2A2A';
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            handleFiles(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFiles(e.target.files[0]);
    });
}

function handleFiles(file) {
    // 1. 형식 체크
    if (!ALLOWED_TYPES.includes(file.type)) {
        alert('이미지(jpg, png, webp) 또는 영상(mp4, mov) 파일만 가능합니다.');
        fileInput.value = '';
        return;
    }

    // 2. 용량 체크 (50MB)
    if (file.size > MAX_FILE_SIZE) {
        alert('파일 용량은 50MB를 넘을 수 없습니다.');
        fileInput.value = '';
        resetPreview();
        return;
    }

    const previewContainer = document.getElementById('file-preview');
    const infoText = dropZone.querySelector('p');
    const icon = dropZone.querySelector('i');
    const isVideo = file.type.startsWith('video/');

    // 파일 읽기 시작
    const reader = new FileReader();
    
    reader.onload = (e) => {
        const fileSrc = e.target.result;

        if (isVideo) {
            // 비디오 요소 생성
            const videoEl = document.createElement('video');
            videoEl.src = fileSrc; // 소스 먼저 할당
            videoEl.preload = 'metadata';

            // 메타데이터 로드 완료 시 실행
            videoEl.onloadedmetadata = function() {
                // 3. 영상 길이 체크 (30초)
                if (videoEl.duration > MAX_VIDEO_DURATION) {
                    alert(`영상 길이는 최대 30초를 초과할 수 없습니다. (현재: ${Math.floor(videoEl.duration)}초)`);
                    fileInput.value = ''; 
                    resetPreview();
                    return;
                }

                // 검증 통과 후 화면 표시
                videoEl.controls = true;
                videoEl.autoplay = true;
                videoEl.muted = true;
                videoEl.classList.add('inner-preview');

                previewContainer.innerHTML = ''; // 기존 내용 삭제
                previewContainer.appendChild(videoEl);
                previewContainer.style.display = 'flex';
                
                if (infoText) infoText.style.display = 'none';
                if (icon) icon.style.display = 'none';
            };
        } else {
            // 이미지일 경우 즉시 표시
            const imgEl = document.createElement('img');
            imgEl.src = fileSrc;
            imgEl.classList.add('inner-preview');

            previewContainer.innerHTML = ''; // 기존 내용 삭제
            previewContainer.appendChild(imgEl);
            previewContainer.style.display = 'flex';
            
            if (infoText) infoText.style.display = 'none';
            if (icon) icon.style.display = 'none';
        }
    };
    
    reader.readAsDataURL(file);
}

function resetPreview() {
    const previewContainer = document.getElementById('file-preview');
    if (previewContainer) {
        previewContainer.innerHTML = '';
        previewContainer.style.display = 'none';
    }
    const infoText = dropZone.querySelector('p');
    const icon = dropZone.querySelector('i');
    if (infoText) infoText.style.display = 'block';
    if (icon) icon.style.display = 'block';
}

// ---------------------------------------------------------
// 7. 신고 제출 로직
// ---------------------------------------------------------
const reportForm = document.getElementById('reportForm');

if (reportForm) {
    reportForm.addEventListener('submit', async (e) => {
        e.preventDefault(); 
        
        const latValue = document.getElementById("latitude").value;
        const lngValue = document.getElementById("longitude").value;

        if (!latValue || !lngValue) {
            if (!confirm("위치를 선택하지 않으셨습니다. 기본 위치로 제출할까요?")) return;
        }

        const submitBtn = reportForm.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true; 
            submitBtn.innerText = '전송 및 AI 분석 중...'; 
            submitBtn.style.opacity = '0.6';
        }

        const formData = new FormData(reportForm);

        try {
            const response = await fetch(reportForm.action, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                alert('신고가 성공적으로 접수되었습니다!');
                window.location.href = '/'; 
            } else {
                alert(result.message || result.error || '전송 중 오류가 발생했습니다.');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerText = '신고 제출하기';
                    submitBtn.style.opacity = '1';
                }
            }
        } catch (error) {
            alert('서버와 통신하는 중 오류가 발생했습니다.');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerText = '신고 제출하기';
                submitBtn.style.opacity = '1';
            }
        }
    });
}