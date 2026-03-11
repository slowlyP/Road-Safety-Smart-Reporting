USE ai_accident_detection;

# 1. users
# 기능: 회원 정보 및 권한 관리
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,

    password_hash VARCHAR(255) NOT NULL,

    name VARCHAR(50),

    role ENUM('user','admin') DEFAULT 'user',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    deleted_at DATETIME
);

# 2. role_requests
# 기능: 일반 회원의 관리자 권한 신청 관리
CREATE TABLE role_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT NOT NULL,

    request_reason TEXT,

    status ENUM('대기','승인','거절') DEFAULT '대기',

    reviewed_by BIGINT,

    reviewed_at DATETIME,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),

    FOREIGN KEY (reviewed_by) REFERENCES users(id)

);

# 3. reports
# 기능: 사용자가 등록한 낙하물 신고 기본 정보
CREATE TABLE reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT NOT NULL,

    title VARCHAR(200) NOT NULL,
    content TEXT,

    report_type ENUM('이미지','영상','카메라'),

    location_text VARCHAR(255),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),

    risk_level ENUM('낮음','주의','위험','긴급') DEFAULT '주의',

    status ENUM('접수','확인중','처리완료','오탐') DEFAULT '접수',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    deleted_at DATETIME,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

# 4. report_files
# 기능: 신고에 첨부된 이미지/영상 파일 저장
CREATE TABLE report_files (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    report_id BIGINT NOT NULL,

    original_name VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,

    file_type ENUM('이미지','영상') NOT NULL,
    file_size BIGINT,

    is_active TINYINT(1) DEFAULT 1,

    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME,

    FOREIGN KEY (report_id) REFERENCES reports(id)
);

# 5. detections
# 기능: AI 낙하물 탐지 결과 저장
DROP TABLE IF EXISTS detections;

CREATE TABLE detections (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    report_id BIGINT NOT NULL,
    file_id BIGINT NOT NULL,

    detected_label VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,

    bbox_x1 INT NOT NULL,
    bbox_y1 INT NOT NULL,
    bbox_x2 INT NOT NULL,
    bbox_y2 INT NOT NULL,

    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (report_id) REFERENCES reports(id),
    FOREIGN KEY (file_id) REFERENCES report_files(id)
);

# 6. alerts
# 기능: 실시간 알림 기록
CREATE TABLE alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    report_id BIGINT,
    detection_id BIGINT,

    alert_level ENUM('낮음','주의','위험','긴급'),

    message VARCHAR(255),

    is_read TINYINT(1) DEFAULT 0,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME,

    FOREIGN KEY (report_id) REFERENCES reports(id),
    FOREIGN KEY (detection_id) REFERENCES detections(id)
);

# 7. report_status_logs
# 기능: 신고 상태 변경 이력 관리
DROP TABLE IF EXISTS report_status_logs;

CREATE TABLE report_status_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    report_id BIGINT NOT NULL,

    old_status ENUM('접수','확인중','처리완료','오탐'),
    new_status ENUM('접수','확인중','처리완료','오탐'),

    changed_by BIGINT,

    memo VARCHAR(255),

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (report_id) REFERENCES reports(id),
    FOREIGN KEY (changed_by) REFERENCES users(id)
);

# 8. admin_logs
# 기능: 관리자 주요 작업 로그 저장
DROP TABLE IF EXISTS admin_logs;

CREATE TABLE admin_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    admin_user_id BIGINT NOT NULL,

    action_type VARCHAR(100) NOT NULL,
    target_type VARCHAR(100) NOT NULL,
    target_id BIGINT,

    action_detail VARCHAR(255),

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (admin_user_id) REFERENCES users(id)
);