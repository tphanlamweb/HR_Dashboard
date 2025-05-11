
# app.py
from flask import Flask, jsonify , render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, DateTime
from extension import db  # Import SQLAlchemy từ extension.py
from datetime import datetime, timezone
import config  # Lấy thông tin kết nối từ file config.py
from auth import requires_role, requires_self_or_role
from models import employees ,salaries,attendance, Employees , Users # Import các model từ models.py
from sqlalchemy import text  # Import text từ SQLAlchemy


app = Flask(__name__)

# Áp dụng cấu hình từ config.py
app.config.from_object(config)

# Khởi tạo SQLAlchemy với app
db.init_app(app)

# Kiểm tra kết nối
with app.app_context():
    try:
        # Thực hiện truy vấn đơn giản đến SQL Server
        sqlserver_engine = db.engines['sqlserver']
        with sqlserver_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Kết nối đến SQL Server thành công!")

        # Thực hiện truy vấn đơn giản đến MySQL
        mysql_engine = db.engines['mysql']
        with mysql_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Kết nối đến MySQL thành công!")

        # Thực hiện truy vấn đơn giản đến HR_DASHBOARD
        userdb_engine = db.engines['userdb']
        with userdb_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Kết nối đến HR_DASHBOARD thành công!")

    except Exception as e:
        print(f"Lỗi kết nối: {e}")


# -------------------- DANH SÁCH SQL SERVER -------------------- chưa có csdl

# Đại diện cho bảng Employees trong CSDL SQL Server    
# class Employees(db.Model):
#     __tablename__ = "Employees"
#     __bind_key__ = "sqlserver"  # Bắt buộc để tránh lỗi UnboundExecutionError
#     EmployeeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     FullName = db.Column(db.String(100), nullable=False)
#     DateOfBirth = db.Column(db.Date, nullable=False)
#     Gender = db.Column(db.String(10))
#     PhoneNumber = db.Column(db.String(15))
#     Email = db.Column(db.String(100))
#     HireDate = db.Column(db.Date , nullable=False)
#     DepartmentID = db.Column(db.Integer)
#     PositionID = db.Column(db.Integer)
#     Status = db.Column(db.String(50))

    
    

# -------------------- DANH SÁCH MYSQL --------------------

# Danh sách nhân viên trong PAYROLL MySQL
# class employees(db.Model):
#     __tablename__ = "employees"
#     __bind_key__ = "mysql"
#     EmployeeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     FullName = db.Column(db.String(100), nullable=False)
#     DepartmentID = db.Column(db.Integer)
#     PositionID = db.Column(db.Integer)
#     Status = db.Column(db.String(50))


# # Danh sách Lương trong PAYROLL MySQL
# class salaries(db.Model):
#     __tablename__ = "salaries"
#     __bind_key__ = "mysql"
#     SalaryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     EmployeeID = db.Column(db.Integer, db.ForeignKey("employees.EmployeeID"))
#     SalaryMonth = db.Column(db.Date)
#     BaseSalary = db.Column(db.Float)
#     Bonus = db.Column(db.Float)
#     Deductions = db.Column(db.Float)
#     NetSalary = db.Column(db.Float)
# # Danh sách chấm công trong PAYROLL MySQL
# class attendance(db.Model):
#     __tablename__ = "attendance"
#     __bind_key__ = "mysql"  # Bắt buộc để tránh lỗi UnboundExecutionError
#     AttendanceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     EmployeeID = db.Column(db.Integer, db.ForeignKey("employees.EmployeeID"))
#     WorkDays = db.Column(db.Integer)
#     AbsentDay = db.Column(db.Integer)
#     LeavesDay = db.Column(db.Integer)
#     AttendanceMon = db.Column(db.Date)


# -------------------- ROUTE: TRANG CHỦ --------------------

# Trang chủ
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Lấy thông tin đăng nhập từ form
        username = request.form.get("username")
        password = request.form.get("password")
        
        print(username, password)  # Debug

        if not username or not password:
            return render_template("login_1.html", error="Tên đăng nhập và mật khẩu là bắt buộc")

        # Truy vấn người dùng từ cơ sở dữ liệu
        user = Users.query.filter_by(User_Name=username, User_Password=password).first()

        if not user:
            return render_template("login_1.html", error="Tên đăng nhập hoặc mật khẩu không đúng")

        # Kiểm tra vai trò và chuyển hướng
        if user.User_Role == 1:  # Admin
            return redirect(url_for("admin_dashboard"))
        elif user.User_Role == 2:  # HR Manager
            return redirect(url_for("hr_dashboard"))
        elif user.User_Role == 3:  # Payroll Manager
            return redirect(url_for("payroll_dashboard"))
        elif user.User_Role == 4:  # Employee
            return redirect(url_for("employee_dashboard"))
        else:
            return render_template("login_1.html", error="Vai trò không hợp lệ")

    # Nếu là GET, hiển thị trang đăng nhập
    return render_template("login_1.html")
@app.route("/admin-dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route("/hr-dashboard")
def hr_dashboard():
    return render_template("hr_dashboard.html")

@app.route("/payroll-dashboard")
def payroll_dashboard():
    return render_template("payroll_dashboard.html")

@app.route("/employee-dashboard")
def employee_dashboard():
    return render_template("employee_dashboard.html")
# -------------------- ROUTE: LẤY DANH SÁCH NHÂN VIÊN --------------------

            
@app.route('/employees', methods=['GET'])
@requires_role('2'or'1')  # Chỉ HR Manager (Role = 2) hoặc Admin (Role = 1) được phép truy cập
@requires_self_or_role('4')  # Nhân viên chỉ xem thông tin của chính họ
def get_employees():
    # IN DANH SÁCH NHÂN VIÊN
    try:
        # Lấy danh sách nhân viên từ SQL Server
        nhan_viens_sql = Employees.query.all()

        # Lấy danh sách nhân viên từ MySQL (bao gồm cả PhongBan và ChucVu)
        nhan_viens_mysql = employees.query.all()

        # Chuyển dữ liệu MySQL thành dictionary để dễ tìm kiếm theo EmployeeID
        mysql_dict = {nv.EmployeeID: nv for nv in nhan_viens_mysql}

        # Danh sách nhân viên kết hợp
        merged_data = []

        for nv_sql in nhan_viens_sql:
            if nv_sql.EmployeeID in mysql_dict:
                nv_mysql = mysql_dict[nv_sql.EmployeeID]
                merged_data.append({
                    "EmployeeID": nv_sql.EmployeeID,
                    "FullName": nv_sql.FullName,
                    "DateOfBirth": nv_sql.DateOfBirth,
                    "PhoneNumber": nv_sql.PhoneNumber,
                    "Email": nv_sql.Email,
                    "HireDate": nv_sql.HireDate,
                    "DepartmentID": getattr(nv_sql, "DepartmentID", "N/A"),
                    "PositionID": getattr(nv_sql, "PositionID", "N/A"),
                    "Status": nv_sql.Status
                })
                del mysql_dict[nv_sql.EmployeeID]  # Xóa để tránh bị lặp lại
            else:
                merged_data.append({
                    "EmployeeID": nv_sql.EmployeeID,
                    "FullName": nv_sql.FullName,
                    "DateOfBirth": nv_sql.DateOfBirth,
                    "PhoneNumber": nv_sql.PhoneNumber,
                    "Email": nv_sql.Email,
                    "HireDate": nv_sql.HireDate,
                    "DepartmentID": getattr(nv_sql, "DepartmentID", "N/A"),
                    "PositionID": getattr(nv_sql, "PositionID", "N/A"),
                    "Status": nv_sql.Status
                })

        # Thêm các nhân viên chỉ có trong MySQL (sau khi loại bỏ trùng lặp)
        for nv_mysql in mysql_dict.values():
            merged_data.append({
                "EmployeeID": nv_mysql.EmployeeID,
                "FullName": nv_mysql.FullName,
                "DepartmentID": nv_mysql.DepartmentID,
                "PositionID": nv_mysql.PositionID,
                "Status": nv_mysql.Status,
                "DateOfBirth": getattr(nv_mysql, "DateOfBirth", "N/A"),
                "PhoneNumber": getattr(nv_mysql, "PhoneNumber", "N/A"),
                "Email": getattr(nv_mysql, "Email", "N/A"),
                "HireDate": getattr(nv_mysql, "HireDate", "N/A")
            })

        return render_template("Add_Employee_2.html", nhan_viens=merged_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------- ROUTE: LẤY DANH SÁCH LƯƠNG (MY SQL) --------------------

@app.route('/payrolls', methods=['GET'])
@requires_role('3'or'1')  # Chỉ Payroll Manager hoặc Admin mới được phép truy cập
@requires_self_or_role('4')  # Nhân viên chỉ xem thông tin của chính họ
def get_payrolls():
    
    # Lấy bảng lương từ MySQL
    payrolls = salaries.query.all()
    
    # Lấy danh sách nhân viên từ SQL Server
    employees = Employees.query.all()


    #####################
    
        # Ghép nhân viên với lương theo EmployeeID
    payroll_list = []
    for nv in employees:
        luong = next((l for l in payrolls if l.EmployeeID == nv.EmployeeID), None)
        if luong:
            payroll_list.append((nv, luong))

    print("Dữ liệu sau khi ghép:", payroll_list)  # Debug

    # Truyền danh sách đã ghép vào template
#    return render_template("in_bang_luong.html", employees = data)
    return render_template("Payroll_Edited.html", luong_nv = payroll_list)

    #####################

# -------------------- ROUTE: THÊM NHÂN VIÊN --------------------

# Trang thêm nhân viên
@app.route("/add-employee", methods=["POST"])
@requires_role('2'or'1')  # Chỉ HR Manager hoặc Admin mới được phép truy cập
def them_nhan_vien():
    if request.method == "POST":
        EmployeeID = request.form[""]
        FullName = request.form[""]
        DateOfBirth = request.form[""]
        Gender = request.form[""]
        PhoneNumber = request.form[""]
        Email = request.form[""]
        HireDate = request.form[""]
        DepartmentID = request.form[""]
        PositionID = request.form[""]
        Status = request.form[""]
        CreateAt = request.form[""]
        UpdateAt = request.form[""]


        # Thêm vào SQL Server
        nhan_vien_sql = Employees(
        Employee_ID = EmployeeID,
        Full_Name = FullName,
        Date_Of_Birth = DateOfBirth,
        gender = Gender,
        Phone_Number = PhoneNumber,
        email = Email,
        Hire_Date = HireDate,
        Department_ID = DepartmentID,
        Position_ID = PositionID,
        status = Status,
        Create_At = CreateAt,
        Update_At = UpdateAt,
        )
        db.session.add(nhan_vien_sql)
        db.session.commit()

        # Thêm vào MySQL
        nhan_vien_mysql = employees(
            Employee_ID=nhan_vien_sql.EmployeeID,  # Lấy mã nhân viên từ SQL Server
            Full_name=FullName,
            Department_ID = DepartmentID,
            Position_ID=PositionID,
            status=Status,
        )
        db.session.add(nhan_vien_mysql)
        db.session.commit()

        return redirect(url_for("index"))

#    return render_template("them_nhan_vien.html")


# -------------------- ROUTE: CẬP NHẬT THÔNG TIN NHÂN VIÊN --------------------

@app.route("/update-employee", methods=["PUT"])
@requires_role('2'or'1') 
def update_employee():
    data = request.get_json()

    # Lấy Employee_ID từ JSON gửi lên
    employee_id = data.get("Employee_ID")

    if not employee_id:
        return jsonify({"error": "Thiếu mã nhân viên"}), 400

    # Tìm nhân viên trong SQL Server
    nhan_vien_sql = Employees.query.filter_by(Employee_ID=employee_id).first()

    # Tìm nhân viên trong MySQL
    nhan_vien_mysql = employees.query.filter_by(Employee_ID=employee_id).first()

    if not nhan_vien_sql or not nhan_vien_mysql:
        return jsonify({"error": "Không tìm thấy nhân viên"}), 404

    # Cập nhật thông tin nhân viên SQL Server
    nhan_vien_sql.Full_Name = data.get("Full_Name", nhan_vien_sql.Full_Name)
    nhan_vien_sql.Date_Of_Birth = data.get("Date_Of_Birth", nhan_vien_sql.Date_Of_Birth)
    nhan_vien_sql.gender = data.get("gender", nhan_vien_sql.gender)
    nhan_vien_sql.Phone_Number = data.get("Phone_Number", nhan_vien_sql.Phone_Number)
    nhan_vien_sql.email = data.get("email", nhan_vien_sql.email)
    nhan_vien_sql.Hire_Date = data.get("Hire_Date", nhan_vien_sql.Hire_Date)
    nhan_vien_sql.Department_ID = data.get("Department_ID", nhan_vien_sql.Department_ID)
    nhan_vien_sql.Position_ID = data.get("Position_ID", nhan_vien_sql.Position_ID)
    nhan_vien_sql.status = data.get("status", nhan_vien_sql.status)
    nhan_vien_sql.Update_At = data.get("Update_At", nhan_vien_sql.Update_At)

    # Cập nhật thông tin trong MySQL
    nhan_vien_mysql.Full_name = data.get("Full_Name", nhan_vien_mysql.Full_name)
    nhan_vien_mysql.Department_ID = data.get("Department_ID", nhan_vien_mysql.Department_ID)
    nhan_vien_mysql.Position_ID = data.get("Position_ID", nhan_vien_mysql.Position_ID)
    nhan_vien_mysql.status = data.get("status", nhan_vien_mysql.status)

    db.session.commit()

    return jsonify({"message": "Cập nhật thông tin nhân viên thành công"}), 200


# -------------------- ROUTE: XÓA THÔNG TIN NHÂN VIÊN --------------------

@app.route("/delete-employee", methods=["DELETE"])
@requires_role('2'or'1')  # Chỉ HR Manager hoặc Admin mới được phép truy cập
def delete_employee():
    data = request.get_json()
    ma_nv = data.get("EmployeeID")

    if not ma_nv:
        return jsonify({"error": "Thiếu EmployeeID"}), 400

    # Kiểm tra nếu nhân viên còn liên kết với bảng lương
    luong_ton_tai = salaries.query.filter_by(EmployeeID=ma_nv).first()
    if luong_ton_tai:
        return jsonify({
            "error": f"Không thể xóa nhân viên {ma_nv} vì đang có dữ liệu lương liên kết."
        }), 400

    # Tìm nhân viên trong hai hệ thống
    nv_sql = Employees.query.filter_by(EmployeeID=ma_nv).first()
    nv_mysql = employees.query.filter_by(EmployeeID=ma_nv).first()

    if not nv_sql and not nv_mysql:
        return jsonify({"error": "Nhân viên không tồn tại trong hệ thống."}), 404

    # Xóa nhân viên ở SQL Server
    if nv_sql:
        db.session.delete(nv_sql)

    # Xóa nhân viên ở MySQL
    if nv_mysql:
        db.session.delete(nv_mysql)

    db.session.commit()

    return jsonify({"message": f"Đã xóa nhân viên {ma_nv} thành công."}), 200


# -------------------- ROUTE: LẤY DỮ LIỆU CHẤM CÔNG --------------------
@app.route("/attendance", methods=["GET"])
@requires_role('3'or'1')  # Chỉ Payroll Manager hoặc Admin mới được phép truy cập
def get_attendance():
    try:
        # Lấy toàn bộ dữ liệu chấm công từ bảng attendance (PAYROLL)
        attendance_list = attendance.query.all()

        # Chuyển đổi thành danh sách dictionary
        data = []
        for att in attendance_list:
            data.append({
                "AttendanceID": att.AttendanceID,
                "EmployeeID": att.EmployeeID,
                "WorkDays": att.WorkDays,
                "AbsentDay": att.AbsentDay,
                "LeavesDay": att.LeavesDay,
                "AttendanceMon": att.AttendanceMon.strftime("%Y-%m-%d") if att.AttendanceMon else None,
                "CreateAt": att.CreateAt.strftime("%Y-%m-%d %H:%M:%S") if att.CreateAt else None
            })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
    # -------------------- ROUTE: BÁO CÁO NHÂN SỰ --------------------

@app.route("/reports", methods=["GET"])
@requires_role('2'or'1')  # Chỉ HR Manager hoặc Admin mới được phép truy cập
def bao_cao_nhan_su():
    # Truy vấn dữ liệu tổng số nhân viên theo phòng ban
    by_department = db.session.query(
        Employees.DepartmentID,
        func.count(Employees.EmployeeID).label("total")
    ).group_by(Employees.DepartmentID).all()

    # Truy vấn dữ liệu tổng số nhân viên theo vị trí
    by_position = db.session.query(
        Employees.PositionID,
        func.count(Employees.EmployeeID).label("total")
    ).group_by(Employees.PositionID).all()

    # Truy vấn dữ liệu tổng số nhân viên theo giới tính
    by_gender = db.session.query(
        Employees.Gender,
        func.count(Employees.EmployeeID).label("total")
    ).group_by(Employees.Gender).all()

    # Truy vấn dữ liệu tổng số nhân viên theo trạng thái (đang làm, nghỉ việc...)
    by_status = db.session.query(
        Employees.Status,
        func.count(Employees.EmployeeID).label("total")
    ).group_by(Employees.Status).all()

    # Chuyển đổi kết quả về dạng từ điển để trả về JSON
    report = {
        "by_department": [{"DepartmentID": d[0], "Total": d[1]} for d in by_department],
        "by_position": [{"PositionID": p[0], "Total": p[1]} for p in by_position],
        "by_gender": [{"Gender": g[0], "Total": g[1]} for g in by_gender],
        "by_status": [{"Status": s[0], "Total": s[1]} for s in by_status],
    }

    return jsonify(report)

@app.route("/reports-page")
def report_page():
    return render_template("reports.html")

# -------------------- CHẠY APP --------------------

if __name__ == '__main__':
    print(app.url_map)
    print(app.config["SQLALCHEMY_DATABASE_URI"])

    app.run(debug=True)

