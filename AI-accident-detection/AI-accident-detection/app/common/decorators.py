# 로그인 여부나 관리자 권한 체크할 때 쓰는 데코레이터

from functools import wraps
from flask import request
from app.common.response import error_response


def login_required(func):
    """
    로그인 여부 확인용 데코레이터
    현재는 임시 예시로 Authorization 헤더 존재 여부만 체크
    나중에 JWT 검증 로직으로 확장 가능
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return error_response(
                message="로그인이 필요합니다.",
                status_code=401
            )

        return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    """
    관리자 권한 체크용 데코레이터
    현재는 임시 예시 구조
    나중에 실제 사용자 role 검사 로직 추가 예정
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_role = request.headers.get("Role")

        if user_role != "admin":
            return error_response(
                message="관리자 권한이 필요합니다.",
                status_code=403
            )

        return func(*args, **kwargs)

    return wrapper