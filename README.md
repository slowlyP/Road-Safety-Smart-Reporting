# 🛣️ AI 기반 도로 사고 스마트 신고 시스템 (Backend)

> **YOLO 객체 탐지와 LLM(Gemini)을 결합하여 도로 위 위험 요소를 실시간으로 분석하고 관리자에게 보고하는 스마트 관제 시스템입니다.**

---

## 🔗 Live Demo
- **접속 주소:** [http://mbc-sw.iptime.org:3201/](http://mbc-sw.iptime.org:3201/)
*(실시간 사고 탐지 및 대시보드 관제가 가능한 배포 환경입니다.)*
<img width="604" height="1028" alt="image" src="https://github.com/user-attachments/assets/3dc9e35e-6b56-423f-b08b-805762438f28" />
<img width="599" height="770" alt="{D60C7333-6592-422F-8EAC-7D264489C0C2}" src="https://github.com/user-attachments/assets/27886eae-acbb-4edc-bf9f-d1b6e9158b0f" />
<img width="1079" height="856" alt="{FEA5737C-943D-49B9-8C38-A34FEC972C9F}" src="https://github.com/user-attachments/assets/5d79329f-9e91-4b5b-a146-269817cc5854" />





---

## 🚀 Key Features (My Contributions)

### 1. AI 분석 및 신고 텍스트 자동화 (Gemini 1.5 Flash)
- **자동화:** 탐지된 객체(낙하물, 사고 등) 정보를 기반으로 신고 제목과 상세 내용을 AI가 자동 생성하여 관제 효율성 극대화.
- **장애 내성 설계:** API 할당량 초과나 네트워크 오류 발생 시에도 시스템이 중단되지 않도록 **Fallback 로직**을 구현하여 서비스 안정성 확보.
- **데이터 매핑:** AI의 영문 라벨을 한국어 표준 데이터로 변환하여 사용자에게 직관적인 정보 제공.
```
# llm_service.py: 장애 내성을 위한 Fallback 로직
try:
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    ) # Gemini API 호출
    return json.loads(response.text)


# API 타임아웃 또는 할당량 초과 시 시스템 중단을 막는 Fallback 처리
except google_exceptions.DeadlineExceeded:
    logger.error("🚨 [LLM 타임아웃] API 응답 시간 초과")
    return fallback_result
except google_exceptions.ResourceExhausted:
    logger.error("🚨 [LLM 할당량 초과] API 사용량 한도 도달")
    return fallback_result

# API 타임아웃 또는 할당량 초과 시 미리 정의된 기본 문구(Fallback) 반환
except google_exceptions.DeadlineExceeded:
    logger.error("🚨 [LLM 타임아웃] API 응답 시간 초과")
    return fallback_result
except google_exceptions.ResourceExhausted:
    logger.error("🚨 [LLM 할당량 초과] API 사용량 한도 도달")
    return fallback_result
```
### 2. 위치 기반 데이터 전처리 (Metadata Extraction)
- **Exif 분석:** 업로드된 이미지/영상에서 위경도 좌표를 추출하여 지도상에 사고 발생 위치를 자동으로 매핑.
- **파일 검증:** 대용량 미디어 파일(50MB 제한) 필터링 및 확장자 체크를 통해 서버 자원 보호 및 보안 강화.

    
```
report_service.py: 서버 리소스 보호를 위한 파일 검증
    class ReportService:
        MAX_FILE_SIZE = 50 * 1024 * 1024 # 50MB 제한
  @staticmethod
    def process_report_submission(user_id, form_data, upload_file):
      # 파일 크기 및 확장자 유효성 검사
      if file_size > ReportService.MAX_FILE_SIZE:
         raise ValueError(f"파일 용량은 50MB를 넘을 수 없습니다.")

      if ext not in ReportService.ALLOWED_EXTENSIONS:
        raise ValueError(f"허용되지 않는 파일 형식입니다: {ext}")
```
  

### 3. 시스템 연동 및 데이터 정합성 설계
- **실시간 연동:** 팀원이 구현한 WebSocket 기반 알림 시스템이 백엔드 로직과 유기적으로 작동하도록 인터페이스 설계.
- **트랜잭션 관리:** 데이터베이스 저장이 최종 성공(`commit`)한 시점에만 실시간 알림이 발송되도록 제어하여, 에러 발생 시 잘못된 알림이 전송되는 혼선 방지.
```
# report_service.py: 데이터 무결성을 위한 트랜잭션 관리
try:
    # 1. DB에 신고 정보 저장 (Transaction 시작)
    db.session.add(new_report)
    db.session.commit() # DB 확정(Commit)

    # 2. DB 저장이 성공한 경우에만 실시간 알림 서비스(WebSocket) 호출
    if realtime_alert_result:
        RealtimeAlertService.emit_realtime_alert(realtime_alert_result["payload"])

except Exception as e:
    db.session.rollback() # 에러 발생 시 DB 원상복구(Rollback)
    if saved_file_path and os.path.exists(saved_file_path):
        os.remove(saved_file_path) # 실패한 데이터의 물리 파일까지 즉시 삭제
```

## 🛠️ Technical Decision
- **Layered Architecture:** `Route - Service - AI Service`로 계층을 분리하여 코드의 독립성과 유지보수성 향상.
- **Error Handling:** 외부 API 의존성을 관리하기 위해 예외 처리를 강화하고, 에러 시 DB 롤백 및 물리 파일 삭제를 연동하여 시스템 청결도 유지.



## 📦 Tech Stack
- **Language:** Python 3.11
- **Framework:** Flask
- **AI:** Google Gemini API, YOLOv8, RT-DETR
- **Database:** MySQL
- **Tool:** Git, GitHub
