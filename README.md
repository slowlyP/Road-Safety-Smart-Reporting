# AI Accident Detection System
스마트폰 카메라로 촬영된 주행 영상을 기반으로 AI가 사고 및 이상징후를 감지하고 분석하는 시스템입니다.
AI 모델을 통해 사고 발생 여부를 1차적으로 판단하며, 사고가 발생하지 않은 경우에도 향후 사고 가능성을 확률 형태로 예측합니다.

또한 WebSocket 기반 실시간 알림 기능을 통해 이상 상황을 사용자에게 즉시 전달하고, 분석 결과를 시각화하여 직관적으로 확인할 수 있도록 하는 웹 서비스 프로젝트입니다.

---

## 주요 기능
- AI 기반 사고 및 이상징후 감지
- 사고 발생 여부 판단 및 위험도 분석
- 스마트폰 영상 업로드 및 영상 관리
- WebSocket 기반 실시간 알림 기능
- 사고 분석 결과 시각화
- 사용자 및 관리자 기능 제공

---

## 기술 스택

**AI**
- Python
- TensorFlow / PyTorch
- OpenCV
**Backend**
- Python (Flask / FastAPI)
**Frontend**
- HTML / CSS / JavaScript
- React (optional)
**Database**
- MySQL
**Real-time Communication**
- WebSocket

---

## Branches 구조
```
main
 ├ feature-ai : AI
 ├ feature-auth :  회원관리
 ├ feature-video :  영상
 ├ feature-db : DB
 └ feature-frontend : 프론트엔드
```
