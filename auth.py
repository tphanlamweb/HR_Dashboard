from functools import wraps
from flask import request, jsonify, session, abort

from enum import Enum

# Khai báo các vai trò cố định trong hệ thống
class UserRole(Enum):
    ADMIN = 1
    HR_MANAGER = 2
    PAYROLL_MANAGER = 3
    EMPLOYEE = 4

    @classmethod
    def from_id(cls, role_id):
        
        # Hàm tiện ích: chuyển số (1, 2, 3, 4) sang Enum tương ứng
        try:
            role_id = int(role_id)  # ép kiểu sang số nguyên
        except ValueError:
                return None
    
        for role in cls:
            if role.value == role_id:
                return role
        return None  # Nếu không khớp, trả về None
    
    

def authorize(allowed_roles=None, allow_self=False):
    """
    Middleware kiểm tra quyền truy cập API.
    - allowed_roles: danh sách vai trò được phép (ví dụ: [UserRole.ADMIN.value])
    - allow_self: nếu True, người dùng được phép truy cập dữ liệu của chính mình
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_role = session.get('role')    # lấy vai trò từ session
            user_id = session.get('user_id')   # lấy ID người dùng từ session

            if user_role is None or user_id is None:
                return abort(401)  # Chưa đăng nhập

            if allow_self:
                # Kiểm tra nếu người dùng đang thao tác chính họ (GET /employees/<id>)
                target_id = kwargs.get('id')
                if str(user_id) != str(target_id) and user_role != UserRole.ADMIN.value:
                    return abort(403)  # Không phải admin và không phải chính mình

            if allowed_roles and user_role not in allowed_roles:
                return abort(403)  # Vai trò không được phép

            return f(*args, **kwargs)
        return wrapper
    return decorator
