from flask import Blueprint, render_template, session, redirect, url_for, request
from app.common.response import success_response, error_response
from app.common.exceptions import BaseCustomException
from app.services.admin_role_request_service import AdminRoleRequestService
from app.repositories.user_repository import UserRepository

admin_role_request_bp = Blueprint(
    "admin_role_request",
    __name__,
    url_prefix="/admin/role-requests"
)


def _check_admin():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        return redirect(url_for("main.index"))

    return None


@admin_role_request_bp.route("/", methods=["GET"])
def role_request_list():
    admin_check = _check_admin()
    if admin_check:
        return admin_check

    admin_user = UserRepository.get_user_by_id(session["user_id"])
    request_list = AdminRoleRequestService.get_role_request_list()

    return render_template(
        "admin/role_request_list.html",
        user=admin_user,
        request_list=request_list
    )


@admin_role_request_bp.route("/<int:request_id>", methods=["GET"])
def role_request_detail(request_id):
    admin_check = _check_admin()
    if admin_check:
        return admin_check

    admin_user = UserRepository.get_user_by_id(session["user_id"])
    role_request = AdminRoleRequestService.get_role_request_detail(request_id)

    return render_template(
        "admin/role_request_detail.html",
        user=admin_user,
        role_request=role_request
    )


@admin_role_request_bp.route("/<int:request_id>/review", methods=["POST"])
def review_role_request(request_id):
    admin_check = _check_admin()
    if admin_check:
        return error_response(message="관리자만 접근할 수 있습니다.", status_code=403)

    try:
        request_data = request.get_json()

        if not request_data:
            return error_response(
                message="요청 데이터가 없습니다.",
                status_code=400
            )

        status = request_data.get("status")
        review_comment = request_data.get("review_comment", "")

        result = AdminRoleRequestService.review_role_request(
            request_id=request_id,
            admin_user_id=session["user_id"],
            status=status,
            review_comment=review_comment
        )

        return success_response(
            message="권한 신청 검토가 완료되었습니다.",
            data={
                "id": result.id,
                "status": result.status
            },
            status_code=200
        )

    except BaseCustomException as e:
        return error_response(
            message=e.message,
            status_code=e.status_code
        )

    except Exception as e:
        return error_response(
            message="권한 신청 검토 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )