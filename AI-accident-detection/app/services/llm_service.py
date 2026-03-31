import os
import json
import logging
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

# 로깅 설정
logger = logging.getLogger(__name__)

# 1. 객체 한글 매핑 (UX 향상: GPT 추천 반영)
LABEL_KR_MAP = {
    "bag": "방치된 포대",
    "box": "박스 낙하물",
    "rock": "낙석",
    "tire": "타이어 파편"
}

# 2. API Key 및 클라이언트 초기화 방어 (GPT 지적 반영)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    logger.critical("🚨 [환경변수 에러] GEMINI_API_KEY가 설정되지 않았습니다.")
    client = None
else:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"🚨 [클라이언트 생성 실패]: {e}")
        client = None

def generate_report_text(detected_objects, location_address="전방 도로"):
    """
    AI 탐지 결과와 위치 정보를 바탕으로 자연스러운 신고 문구를 생성합니다.
    """
    # 3. 탐지 객체가 없는 경우 (Safe Guard)
    if not detected_objects:
        return {
            "title": "도로 안전 점검 알림",
            "content": "특이사항이 발견되지 않았으나 안전 운행하시기 바랍니다."
        }
    
    # 영문 라벨 -> 한글 변환
    objects_kr = [LABEL_KR_MAP.get(str(obj), str(obj)) for obj in detected_objects]
    objects_str = ", ".join(objects_kr)

    # 4. 기본 반환값 (Fallback: GPT가 칭찬한 구조 유지)
    fallback_result = {
        "title": f"[주의] {objects_str} 발견",
        "content": f"{location_address} 인근에 {objects_str}이(가) 확인되었습니다. 주의 운전 바랍니다."
    }

    # 클라이언트가 없으면 즉시 fallback 반환
    if not client:
        return fallback_result

    # 5. 프롬프트 고도화 (위치 정보 포함)
    prompt = f"""
    당신은 도로 안전 관리 전문 AI입니다. 
    현재 '{location_address}' 부근에서 '{objects_str}'이(가) 탐지되었습니다.
    
    운전자들이 즉시 위험을 인지하고 조심할 수 있도록 자연스러운 경고문을 작성하세요.
    - 말투: "탐지되었습니다" 같은 로봇 말투 금지. "주의 바랍니다", "확인되었습니다" 등 사용.
    - 조건: 제목 20자 이내, 내용 100자 이내, JSON 형식 준수.
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
            ),
            request_options={"timeout": 10}
        )

        if not response or not getattr(response, "text", None):
            raise ValueError("AI 응답이 유효하지 않습니다.")

        return json.loads(response.text)

    # 8. 타입 기반 예외 처리 (최종 완성)
    except google_exceptions.DeadlineExceeded:
        logger.error("🚨 [LLM 타임아웃] API 응답 시간이 초과되었습니다.")
        return fallback_result

    except google_exceptions.ResourceExhausted:
        logger.error("🚨 [LLM 할당량 초과] API 사용량이 너무 많습니다.")
        return fallback_result

    except json.JSONDecodeError as e:
    # response 변수가 존재하는지 + text 속성이 있는지 안전하게 확인
        raw_content = "응답 없음"
        if 'response' in locals() and hasattr(response, 'text'):
            raw_content = response.text
        logger.error(f"🚨 [LLM JSON 파싱 에러] {e} | 원본: {raw_content}")
        return fallback_result

    except Exception as e:
        logger.error(f"🚨 [LLM 알 수 없는 에러]: {e}")
        return fallback_result