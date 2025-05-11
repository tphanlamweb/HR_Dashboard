from functools import wraps
from flask import request, jsonify
from extension import db  # Import SQLAlchemy từ config.py
from models import Users  # Import bảng Users từ models.py

# Middleware bảo vệ API: Nhân viên chỉ xem được thông tin của họ
def requires_self_or_role(role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Lấy UserID từ header
            user_id = request.headers.get('UserID')
            if not user_id:
                return jsonify({'error': 'UserID is required'}), 400

            # Lấy ID được yêu cầu từ URL
            requested_id = kwargs.get('id')

            # Truy vấn người dùng từ cơ sở dữ liệu
            user = Users.query.filter_by(Users_ID=user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # Nếu vai trò là 'employee', chỉ cho phép truy cập thông tin của chính họ
            if str(user.User_Role) == '4' and str(user_id) != str(requested_id):
                return jsonify({'error': 'Access denied'}), 403

            # Kiểm tra quyền truy cập theo vai trò
            if str(user.User_Role) != str(role) and str(user.User_Role) != '1':  # '1' là Admin
                return jsonify({'error': 'Access denied'}), 403

            return f(*args, **kwargs)
        return wrapped
    return decorator

# Middleware kiểm tra quyền truy cập theo vai trò
def requires_role(role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Lấy UserID từ header
            user_id = request.headers.get('UserID')
            if not user_id:
                return jsonify({'error': 'UserID is required'}), 400

            # Truy vấn vai trò người dùng từ cơ sở dữ liệu
            user = Users.query.filter_by(Users_ID=user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # Kiểm tra vai trò
            if str(user.User_Role) != str(role):
                return jsonify({'error': 'Access denied'}), 403

            return f(*args, **kwargs)
        return wrapped
    return decorator


def authenticate_user():
    """
    Xác thực người dùng và kiểm tra vai trò từ cơ sở dữ liệu.
    """
    try:
        # Lấy thông tin đăng nhập từ request (username và password)
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Tên đăng nhập và mật khẩu là bắt buộc'}), 400

        # Truy vấn người dùng từ cơ sở dữ liệu
        user = Users.query.filter_by(User_Name=username, User_Password=password).first()

        if not user:
            return jsonify({'error': 'Tên đăng nhập hoặc mật khẩu không đúng'}), 401

        # Trả về thông tin người dùng và vai trò
        return jsonify({
            'message': 'Đăng nhập thành công',
            'UserID': user.Users_ID,
            'Role': user.User_Role
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500