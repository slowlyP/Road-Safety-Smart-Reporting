"""
회원관리(Auth) 라우트

이 파일은 회원가입 / 로그인 관련 HTTP 요청을 처리한다.

주요 기능
- POST /auth/signup  : 회원가입
- POST /auth/login   : 로그인
"""

from flask import Blueprint, request
from marshmallow import ValidationError

from app.schemas.auth_schema import SignupSchema, LoginSchema
from app.services.auth_service import AuthService
from app.common.response import success_response, error_response
from app.common.exceptions import BaseCustomException

# auth 블루프린트 생성
# url_prefix="/auth" 이므로 실제 주소는 /auth/signup, /auth/login 형태가 된다.
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    회원가입 API

    요청 예시(JSON)
    {
        "username": "doha",
        "email": "doha@test.com",
        "password": "1234",
        "name": "김도하"
    }

    처리 순서
    1. request에서 JSON 데이터 받기
    2. SignupSchema로 입력값 검증
    3. AuthService.signup() 호출
    4. 성공 응답 반환
    """

    try:
        # -----------------------------
        # 요청 데이터 받기
        # -----------------------------
        request_data = request.get_json()

        # JSON이 비어 있거나 없는 경우
        if not request_data:
            return error_response(
                message="요청 데이터가 없습니다.",
                status_code=400
            )

        # -----------------------------
        # 입력값 검증
        # -----------------------------
        validated_data = SignupSchema().load(request_data)

        # -----------------------------
        # 회원가입 처리
        # -----------------------------
        user = AuthService.signup(validated_data)

        # -----------------------------
        # 성공 응답
        # 비밀번호 해시값은 응답에 포함하지 않음
        # -----------------------------
        return success_response(
            message="회원가입이 완료되었습니다.",
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "role": user.role
            },
            status_code=201
        )

    except ValidationError as e:
        # marshmallow 검증 실패
        return error_response(
            message="입력값 검증 실패",
            errors=e.messages,
            status_code=400
        )

    except BaseCustomException as e:
        # 서비스에서 발생시킨 커스텀 예외 처리
        return error_response(
            message=e.message,
            status_code=e.status_code
        )

    except Exception as e:
        # 예상하지 못한 서버 내부 에러
        return error_response(
            message="회원가입 처리 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    로그인 API

    login_id에는 username 또는 email 둘 다 들어올 수 있다.

    요청 예시(JSON)
    {
        "login_id": "doha",
        "password": "1234"
    }

    또는

    {
        "login_id": "doha@test.com",
        "password": "1234"
    }

    처리 순서
    1. request에서 JSON 데이터 받기
    2. LoginSchema로 입력값 검증
    3. AuthService.login() 호출
    4. 성공 응답 반환

    현재 단계에서는 JWT 발급 없이 사용자 정보만 반환
    나중에 JWT/세션 처리 추가 가능
    """

    try:
        # -----------------------------
        # 요청 데이터 받기
        # -----------------------------
        request_data = request.get_json()

        if not request_data:
            return error_response(
                message="요청 데이터가 없습니다.",
                status_code=400
            )

        # -----------------------------
        # 입력값 검증
        # -----------------------------
        validated_data = LoginSchema().load(request_data)

        # -----------------------------
        # 로그인 처리
        # -----------------------------
        user = AuthService.login(validated_data)

        # -----------------------------
        # 성공 응답
        # 현재는 사용자 기본 정보만 반환
        # 추후 JWT 토큰 발급 시 token 필드 추가 가능
        # -----------------------------
        return success_response(
            message="로그인에 성공했습니다.",
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "role": user.role
            },
            status_code=200
        )

    except ValidationError as e:
        return error_response(
            message="입력값 검증 실패",
            errors=e.messages,
            status_code=400
        )

    except BaseCustomException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code
        )

    except Exception as e:
        return error_response(
            message="로그인 처리 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )