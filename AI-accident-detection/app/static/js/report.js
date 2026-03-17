let map;
let marker;
let geocoder;
let autocomplete;

// 1. 구글 지도 및 검색(Autocomplete) 초기화
function initMap() {
    const initialPos = { lat: 37.5665, lng: 126.9780 }; // 서울 기준
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

    // [검색 기능 핵심] 주소 자동완성 설정
    initAutocomplete();

    // 마커 드래그 끝났을 때 주소 업데이트
    google.maps.event.addListener(marker, 'dragend', function() {
        updatePosition(marker.getPosition());
    });

    // 지도 클릭 시 마커 이동 및 주소 업데이트
    map.addListener("click", (e) => {
        marker.setPosition(e.latLng);
        updatePosition(e.latLng);
    });
}

// 2. 주소 검색(자동완성) 기능
function initAutocomplete() {
    const input = document.getElementById("location_text");
    // 구글 장소 자동완성 연결
    autocomplete = new google.maps.places.Autocomplete(input);
    // 검색 결과가 바뀌었을 때 실행
    autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.geometry.location) {
            console.log("결과가 없습니다.");
            return;
        }

        // 지도를 검색 위치로 이동
        map.setCenter(place.geometry.location);
        map.setZoom(17);
        marker.setPosition(place.geometry.location);
        // hidden input(위도/경도) 업데이트
        document.getElementById("latitude").value = place.geometry.location.lat();
        document.getElementById("longitude").value = place.geometry.location.lng();
    });
}

// 3. 좌표 및 주소 텍스트 업데이트
function updatePosition(latLng) {
    const lat = latLng.lat();
    const lng = latLng.lng();

    document.getElementById("latitude").value = lat;
    document.getElementById("longitude").value = lng;

    // 역지오코딩: 좌표를 주소 문자열로 변환
    geocoder.geocode({ location: latLng }, (results, status) => {
        if (status === "OK" && results[0]) {
            document.getElementById("location_text").value = results[0].formatted_address;
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
    closeMapModal();
}

// 5. 내 현재 위치 찾기
function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            const pos = { lat: position.coords.latitude, lng: position.coords.longitude };
            map.setCenter(pos);
            map.setZoom(17);
            marker.setPosition(pos);
            updatePosition(new google.maps.LatLng(pos.lat, pos.lng));
        });
    }
}

// ---------------------------------------------------------
// 6. 파일 업로드 및 영상 정보(길이 등) 표시
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
    const previewContainer = document.getElementById('file-preview');
    const infoText = dropZone.querySelector('p');
    const icon = dropZone.querySelector('i');
    previewContainer.innerHTML = '';
    const isVideo = file.type.startsWith('video/');

    const reader = new FileReader();
    reader.onload = (e) => {
        let el;
        if (isVideo) {
            el = document.createElement('video');
            el.controls = true; // 영상 컨트롤러(재생시간 등) 표시
            el.autoplay = true;
            el.muted = true;
            // 영상이 로드되면 길이를 출력 (콘솔이나 UI에 활용 가능)
            el.onloadedmetadata = function() {
                console.log("영상 길이: " + el.duration.toFixed(2) + "초");
            };
        } else {
            el = document.createElement('img');
        }

        el.src = e.target.result;
        el.classList.add('inner-preview');
        previewContainer.appendChild(el);
        previewContainer.style.display = 'flex';
        if (infoText) infoText.style.display = 'none';
        if (icon) icon.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

// --- [새로 추가] 신고 제출 및 후속 처리 로직 ---
const reportForm = document.getElementById('reportForm');

if (reportForm) {
    reportForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // 기본 제출 동작(JSON만 뜨는 현상) 방지

        const formData = new FormData(reportForm);

        try {
            // 서버에 데이터 전송
            const response = await fetch(reportForm.action, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                // 성공 시 알림창을 띄우고 메인 페이지로 이동
                alert('신고가 성공적으로 접수되었습니다!');
                window.location.href = '/'; // 또는 원하는 페이지 주소
            } else {
                // 서버에서 에러 메시지를 보낸 경우
                alert(result.error || '전송 중 오류가 발생했습니다.');
            }
        } catch (error) {
            console.error('네트워크 에러:', error);
            alert('서버와 통신하는 중 오류가 발생했습니다.');
        }
    });
}