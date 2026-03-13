"""
관리자 회원 관리 서비스

역할
- 회원 목록 조회
- 회원 권한 변경
- 회원 삭제
"""

from app.extensions import db
from app.models.user_model import User


class AdminUserService:

    def get_user_list(self):
        """
        전체 회원 목록 조회
        """

        users = (
            User.query
            .filter(User.deleted_at.is_(None))
            .order_by(User.created_at.desc())
            .all()
        )

        result = []

        for u in users:
            result.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "name": u.name,
                "role": u.role,
                "created_at": u.created_at
            })

        return result


    def update_user_role(self, user_id, role):
        """
        회원 권한 변경
        """

        user = User.query.get_or_404(user_id)

        user.role = role

        db.session.commit()

        return user


    def delete_user(self, user_id):
        """
        회원 삭제 (soft delete)
        """

        user = User.query.get_or_404(user_id)

        user.deleted_at = db.func.now()

        db.session.commit()

        return user