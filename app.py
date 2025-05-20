# app.py
from flask import Flask, jsonify , render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, func, DateTime, desc
from dateutil.relativedelta import relativedelta

from sqlalchemy import func, DateTime
from datetime import datetime, timezone, date
import config
from functools import wraps
from flask import session, redirect, url_for, abort
from auth import UserRole, authorize
import logging
logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
app.secret_key = 'thanh-phan-dep-chai-so-1'

# Khai báo nhiều kết nối CSDL thông qua SQLAlchemy binds
app.config['SQLALCHEMY_BINDS'] = {
    'sqlserver': config.SQL_SERVER_CONN,
    'mysql': config.MYSQL_CONN,
    'sqlserver_user': config.SQL_SERVER_USER_CONN
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo SQLAlchemy
db = SQLAlchemy(app)

# -------------------- DANH SÁCH MODELS --------------------

# Đại diện cho bảng Employees trong CSDL SQL Server
class Employees(db.Model):
    __tablename__ = "Employees"
    __bind_key__ = "sqlserver"
    EmployeeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FullName = db.Column(db.String(100), nullable=False)
    DateOfBirth = db.Column(db.Date, nullable=False)
    Gender = db.Column(db.String(10))
    PhoneNumber = db.Column(db.String(15))
    Email = db.Column(db.String(100))
    HireDate = db.Column(db.Date , nullable=False)
    DepartmentID = db.Column(db.Integer)
    PositionID = db.Column(db.Integer)
    Status = db.Column(db.String(50))

class Users(db.Model):
    __tablename__ = "Users"
    __bind_key__ = "sqlserver_user" 
    Users_ID = db.Column(db.Integer, primary_key=True)
    User_Name = db.Column(db.String(225), nullable=False)
    User_Password = db.Column(db.String(225))
    User_Role = db.Column(db.String(225))


class Department(db.Model): 
    __tablename__ = "Departments" 
    __bind_key__ = "sqlserver"
    DepartmentID = db.Column(db.Integer, primary_key=True)
    DepartmentName = db.Column(db.String(225), nullable=False)

class Position(db.Model): 
    __tablename__ = "Positions" 
    __bind_key__ = "sqlserver"
    PositionID = db.Column(db.Integer, primary_key=True)
    PositionName = db.Column(db.String(225), nullable=False)


# Danh sách nhân viên trong PAYROLL MySQL
class employees(db.Model):
    __tablename__ = "employees"
    __bind_key__ = "mysql"
    EmployeeID = db.Column(db.Integer, primary_key=True)
    FullName = db.Column(db.String(100), nullable=False)
    DepartmentID = db.Column(db.Integer)
    PositionID = db.Column(db.Integer)
    Status = db.Column(db.String(50))


# Danh sách Lương trong PAYROLL MySQL
class salary(db.Model): 
    __tablename__ = "salaries" 
    __bind_key__ = "mysql"
    SalaryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.Integer, db.ForeignKey("employees.EmployeeID")) 
    SalaryMonth = db.Column(db.Date)
    BaseSalary = db.Column(db.Float)
    Bonus = db.Column(db.Float)
    Deductions = db.Column(db.Float)
    NetSalary = db.Column(db.Float)

# Danh sách chấm công trong PAYROLL MySQL
class Attendance(db.Model): 
    __tablename__ = "attendance" 
    __bind_key__ = "mysql"
    AttendanceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.Integer, db.ForeignKey("employees.EmployeeID")) 
    WorkDays = db.Column(db.Integer)
    AbsentDays = db.Column(db.Integer)
    LeaveDays = db.Column(db.Integer)
    AttendanceMonth = db.Column(db.Date)
    CreatedAt = db.Column("CreatedAt", db.DateTime, default=datetime.now(timezone.utc)) 


class departments_mysql(db.Model): 
    __tablename__ = "departments" 
    __bind_key__ = "mysql"
    DepartmentID = db.Column(db.Integer, primary_key=True)
    DepartmentName = db.Column(db.String(225), nullable=False)

class positions_mysql(db.Model): 
    __tablename__ = "positions"
    __bind_key__ = "mysql"
    PositionID = db.Column(db.Integer, primary_key=True)
    PositionName = db.Column(db.String(225), nullable=False)


# -------------------- ROUTE: TRANG CHỦ (LOGIN) --------------------

# Trang chủ
@app.route("/" , methods = ['GET','POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Tìm người dùng trong database dựa trên username
        user = Users.query.filter_by(User_Name=username).first()

        if user and user.User_Password == password:
            role_enum = UserRole.from_id(user.User_Role)

            logging.debug(f"Vai trò từ DB cho {username}: {user.User_Role}")

            session['user_id'] = user.Users_ID
            session['username'] = user.User_Name

            if not role_enum:
                logging.warning(f" Không xác định được vai trò cho người dùng: {username} với role_id = {user.User_Role}")
                # Thông báo lỗi cho người dùng
                return render_template('login_1.html', error='Tài khoản có vai trò không hợp lệ')

            session['role'] = role_enum.value # Lưu vai trò dưới dạng số (1, 2, 3, 4)
            logging.debug(f"Vai trò lưu trong session cho {username}: {session['role']}")

            # Chuyển hướng dựa trên vai trò
            if session['role'] in [UserRole.ADMIN.value, UserRole.HR_MANAGER.value]:
                return redirect(url_for('get_employees')) 
            elif session['role'] == UserRole.EMPLOYEE.value:
                return redirect(url_for('only_employee'))
            else:
                logging.warning(f" Vai trò không xác định sau khi chuyển đổi cho {username}: {session['role']}")
                return render_template('login_1.html', error='Tài khoản có vai trò không xác định')


        logging.warning(f" Đăng nhập thất bại cho username: {username}")
        return render_template('login_1.html', error='Sai tên đăng nhập hoặc mật khẩu')

    return render_template("login_1.html")


# -------------------- EMPLOYEE - ROUTE: ROUTE LẤY THÔNG TIN CỦA NHÂN VIÊN --------------------
@app.route('/only-employee', methods=['GET'])
@authorize(allowed_roles=[UserRole.EMPLOYEE.value])
def only_employee():

    # Tạm thời chỉ render trang
    return render_template("staff_employee.html")





# Route hiển thị danh sách nhân viên (chỉ GET)
@app.route('/employees', methods=['GET'])
@authorize(allowed_roles=[UserRole.HR_MANAGER.value, UserRole.ADMIN.value])
def get_employees():
# IN DANH SÁCH NHÂN VIÊN
    # Lấy danh sách phòng ban và vị trí từ SQL Server 
    departments = Department.query.all()
    positions = Position.query.all()

    # Tạo từ điển tra cứu tên phòng ban và vị trí theo ID 
    department_dict = {dept.DepartmentID: dept.DepartmentName for dept in departments}
    position_dict = {pos.PositionID: pos.PositionName for pos in positions}


    # Lấy danh sách nhân viên từ SQL Server
    nhan_viens_sql = Employees.query.all()

    # Lấy danh sách nhân viên từ MySQL
    nhan_viens_mysql = employees.query.all()

    # Chuyển dữ liệu MySQL thành dictionary
    mysql_dict = {nv.EmployeeID: nv for nv in nhan_viens_mysql}

    # Danh sách nhân viên kết hợp
    merged_data = []

    # Lặp qua danh sách từ SQL Server
    for nv_sql in nhan_viens_sql:
        # Tra cứu tên phòng ban và vị trí từ ID 
        department_name = department_dict.get(nv_sql.DepartmentID, "N/A")
        position_name = position_dict.get(nv_sql.PositionID, "N/A")

        data_row = {
            "EmployeeID": nv_sql.EmployeeID,
            "FullName": nv_sql.FullName,
            "DateOfBirth": nv_sql.DateOfBirth,
            "Gender": nv_sql.Gender,
            "PhoneNumber": nv_sql.PhoneNumber,
            "Email": nv_sql.Email,
            "HireDate": nv_sql.HireDate,
            # Thêm tên phòng ban và vị trí, giữ lại ID nếu cần cho form/JS 
            "DepartmentID": nv_sql.DepartmentID, 
            "DepartmentName": department_name,   
            "PositionID": nv_sql.PositionID,     
            "PositionName": position_name,      
            "Status": nv_sql.Status 
        }

        # Cập nhật thêm thông tin từ MySQL nếu có 
        if nv_sql.EmployeeID in mysql_dict:
             del mysql_dict[nv_sql.EmployeeID]

        merged_data.append(data_row)

    # Thêm các nhân viên chỉ có trong MySQL 
    for nv_mysql in mysql_dict.values():
         # Gán tên phòng ban và vị trí là N/A cho nhân viên chỉ có trong MySQL ***
         merged_data.append({
                "EmployeeID": nv_mysql.EmployeeID,
                "FullName": nv_mysql.FullName,
                "DepartmentID": nv_mysql.DepartmentID,
                "DepartmentName": department_dict.get(nv_mysql.DepartmentID, "N/A"),
                "PositionID": nv_mysql.PositionID,     
                "PositionName": position_dict.get(nv_mysql.PositionID, "N/A"),
                "Status": nv_mysql.Status,
                # Các trường này sẽ là N/A vì chúng không có trong mô hình employees MySQL
                "DateOfBirth": "N/A",
                "PhoneNumber": "N/A",
                "Email": "N/A",
                "HireDate": "N/A",
        })

    return render_template("Add_Employee_2.html", nhan_viens=merged_data, departments=departments, positions=positions)
# -------------------- ROUTE: LẤY DANH SÁCH LƯƠNG (MY SQL) --------------------

@app.route('/payrolls', methods=['GET'])
@authorize(allowed_roles=[UserRole.PAYROLL_MANAGER.value, UserRole.ADMIN.value])
def get_payrolls():
    payroll_list = []
    all_salaries_data = []
    all_attendance_data = []

    try:
        # Lấy tất cả bản ghi lương và nhóm theo EmployeeID để lấy bản ghi mới nhất cho bảng chính 
        all_salaries_objects = salary.query.order_by(salary.EmployeeID, desc(salary.SalaryMonth)).all()
        logging.debug(f"Fetched {len(all_salaries_objects)} total salary entries from MySQL.")

        # Tạo dictionary để lưu bản ghi lương mới nhất cho mỗi EmployeeID
        latest_salaries_dict = {}
        for s in all_salaries_objects:
            # Nếu EmployeeID chưa có trong dict hoặc bản ghi hiện tại mới hơn
            if s.EmployeeID not in latest_salaries_dict:
                latest_salaries_dict[s.EmployeeID] = s

        logging.debug(f"Found {len(latest_salaries_dict)} latest salary entries for unique employees.")


        # Lấy danh sách nhân viên từ SQL Server
        employees_list = Employees.query.all()
        logging.debug(f"Fetched {len(employees_list)} employees from SQL Server (for main table).")

        # Ghép nhân viên với bản ghi lương MỚI NHẤT theo EmployeeID 
        employees_dict = {emp.EmployeeID: emp for emp in employees_list}
        logging.debug(f"Created employee dictionary with {len(employees_dict)} entries.")

        # Lặp qua các bản ghi lương mới nhất đã lọc
        for employee_id, luong_moi_nhat in latest_salaries_dict.items():
            # Tìm nhân viên tương ứng từ SQL Server
            nhan_vien_sql = employees_dict.get(employee_id)

            # Chỉ thêm vào danh sách nếu tìm thấy nhân viên trong SQL Server
            if nhan_vien_sql:
                # Tạo một dict kết hợp thông tin từ cả hai
                payroll_entry = {
                    "EmployeeID": luong_moi_nhat.EmployeeID,
                    "FullName": nhan_vien_sql.FullName, 
                    "SalaryMonth": luong_moi_nhat.SalaryMonth,
                    "BaseSalary": luong_moi_nhat.BaseSalary,
                    "Bonus": luong_moi_nhat.Bonus,
                    "Deductions": luong_moi_nhat.Deductions,
                    "NetSalary": luong_moi_nhat.NetSalary,
                    "SalaryID": luong_moi_nhat.SalaryID
                }
                payroll_list.append(payroll_entry)
            else:
                 logging.warning(f"Không tìm thấy nhân viên SQL Server cho EmployeeID: {employee_id} trong bảng lương MySQL (cho bảng chính)")

        logging.debug(f"Final payroll_list contains {len(payroll_list)} entries after merging (for main table).")

        # Lấy TOÀN BỘ dữ liệu lương lịch sử từ MySQL cho modal
        # Sử dụng all_salaries_objects đã lấy ở trên
        all_salaries_data = [{
            "EmployeeID": s.EmployeeID,
            "SalaryID": s.SalaryID,
            "SalaryMonth": s.SalaryMonth.strftime('%Y-%m-%d') if s.SalaryMonth else None, # Định dạng ngày tháng
            "BaseSalary": s.BaseSalary,
            "Bonus": s.Bonus,
            "Deductions": s.Deductions,
            "NetSalary": s.NetSalary,
        } for s in all_salaries_objects]
        logging.debug(f"Prepared {len(all_salaries_data)} historical salary entries for modal.")


        # Lấy TOÀN BỘ dữ liệu chấm công từ MySQL cho modal
        all_attendance_objects = Attendance.query.all()

        all_attendance_data = [{
            "AttendanceID": a.AttendanceID,
            "EmployeeID": a.EmployeeID,
            "WorkDays": a.WorkDays,
            "AbsentDays": a.AbsentDays,
            "LeaveDays": a.LeaveDays,
            "AttendanceMonth": a.AttendanceMonth.strftime('%Y-%m-%d') if a.AttendanceMonth else None,
        } for a in all_attendance_objects]
        logging.debug(f"Fetched {len(all_attendance_data)} attendance entries from MySQL (for modal).")


        # Truyền cả ba danh sách dữ liệu đến template
        return render_template(
            "salary.html",
            luong_nv=payroll_list, # Dữ liệu cho bảng chính
            all_salaries=all_salaries_data, # Toàn bộ lịch sử lương 
            all_attendance=all_attendance_data # Toàn bộ dữ liệu chấm công 
        )
        

    except Exception as e:
        logging.error(f" LỖI KHI LẤY DANH SÁCH LƯƠNG: {e}", exc_info=True)
        # Trả về thông báo lỗi thân thiện hơn
        return render_template(
            "error.html",
            error_message=f"Đã xảy ra lỗi khi tải dữ liệu lương: {e}",
            luong_nv=[],
            all_salaries=[],
            all_attendance=[]
        ), 500

# -------------------- ROUTE: THÊM NHÂN VIÊN --------------------

@app.route("/add-employee", methods=["POST"])
@authorize(allowed_roles=[UserRole.HR_MANAGER.value, UserRole.ADMIN.value])
def add_employee():
    logging.debug("### Bắt đầu xử lý request POST đến /add-employee ###")
    if request.method == "POST":
        try:
            # Lấy dữ liệu từ form và xử lý an toàn 
            FullName = request.form.get("full_name")
            DateOfBirth_str = request.form.get("dob")
            Gender = request.form.get("gender") if request.form.get("gender") else None
            PhoneNumber = request.form.get("phone") if request.form.get("phone") else None
            Email = request.form.get("email") if request.form.get("email") else None
            HireDate = date.today()
            Status = request.form.get("status") if request.form.get("status") else None

            DepartmentID_str = request.form.get("department_id")
            PositionID_str = request.form.get("position_id")

            DepartmentID = None
            if DepartmentID_str:
                try:
                    DepartmentID = int(DepartmentID_str)
                except ValueError:
                    logging.warning(f"Thêm: DepartmentID không hợp lệ '{DepartmentID_str}', gán None.")
                    DepartmentID = None

            PositionID = None
            if PositionID_str:
                try:
                    PositionID = int(PositionID_str)
                except ValueError:
                    logging.warning(f"Thêm: PositionID không hợp lệ '{PositionID_str}', gán None.")
                    PositionID = None

            DateOfBirth = None
            if DateOfBirth_str:
                 try:
                    DateOfBirth = datetime.strptime(DateOfBirth_str, '%Y-%m-%d').date()
                 except ValueError:
                     logging.error(f" Lỗi thêm: Định dạng ngày sinh không hợp lệ: {DateOfBirth_str}")
                     return redirect(url_for("get_employees"))

            # --- Kiểm tra dữ liệu bắt buộc ---
            if not FullName:
                 logging.error(" Lỗi thêm: FullName bị trống.")
                 return redirect(url_for("get_employees"))
            if not DateOfBirth:
                 logging.error(" Lỗi thêm: Ngày sinh bị trống hoặc không hợp lệ sau chuyển đổi.")
                 return redirect(url_for("get_employees"))


            # Thêm vào SQL Server
            logging.debug("Đang tạo đối tượng Employees (SQL Server).")
            nhan_vien_sql = Employees(
                FullName=FullName,
                DateOfBirth=DateOfBirth,
                Gender=Gender,
                PhoneNumber=PhoneNumber,
                Email=Email,
                HireDate=HireDate,
                DepartmentID = DepartmentID,
                PositionID = PositionID,
                Status = Status
            )
            db.session.add(nhan_vien_sql)
            logging.debug("Đã thêm đối tượng Employees vào session.")

            # Flush session để gửi INSERT đến SQL Server và lấy ID được sinh ra 
            db.session.flush()
            logging.debug(f"Đã flush session SQL Server. ID được sinh ra: {nhan_vien_sql.EmployeeID}")

            # Thêm vào MySQL 
            # Lấy ID vừa được SQL Server sinh ra
            mysql_employee_id = nhan_vien_sql.EmployeeID
            logging.debug(f"Đang tạo đối tượng employees (MySQL) với ID từ SQL Server: {mysql_employee_id}")
            nhan_vien_mysql = employees(
                EmployeeID=mysql_employee_id, # Sử dụng ID từ SQL Server
                FullName=FullName,
                DepartmentID=DepartmentID,
                PositionID=PositionID,
                Status=Status
            )
            db.session.add(nhan_vien_mysql)
            logging.debug("Đã thêm đối tượng employees vào session.")


            logging.debug("Đang cố gắng commit session...")
            db.session.commit()
            logging.debug(" Commit thành công!")


        except Exception as e:
            db.session.rollback()
            
            logging.error(f" LỖI KHI THÊM NHÂN VIÊN: {e}", exc_info=True)
            return f"Đã xảy ra lỗi khi thêm nhân viên: {e}", 500 

    # Chuyển hướng trở lại trang danh sách nhân viên sau khi xử lý
    logging.debug("Chuyển hướng về /employees")
    return redirect(url_for("get_employees"))



# -------------------- ROUTE: CẬP NHẬT THÔNG TIN NHÂN VIÊN --------------------
@app.route("/update-employee", methods=["POST"])
@authorize(allowed_roles=[UserRole.HR_MANAGER.value, UserRole.ADMIN.value])
def update_employee():
    logging.debug("### Bắt đầu xử lý request POST đến /update-employee ###")
    if request.method == "POST":
        try:
            # Lấy dữ liệu từ form bằng các thuộc tính name
            employee_id_str = request.form.get("employee_id")
            FullName = request.form.get("full_name")
            DateOfBirth_str = request.form.get("dob")
            Gender = request.form.get("gender")
            PhoneNumber = request.form.get("phone") 
            Email = request.form.get("email") 
            Status = request.form.get("status") 
            DepartmentID_str = request.form.get("department_id")
            PositionID_str = request.form.get("position_id")


            # EmployeeID là bắt buộc
            if not employee_id_str:
                 logging.error(" Lỗi cập nhật: Thiếu EmployeeID trong form")
                 return redirect(url_for("get_employees"))

            try:
                employee_id = int(employee_id_str)
                logging.debug(f"Đang cập nhật nhân viên với ID: {employee_id}")
            except ValueError:
                 logging.error(f" Lỗi cập nhật: EmployeeID không hợp lệ: {employee_id_str}")
                 return redirect(url_for("get_employees"))

            # FullName 
            if not FullName:
                 logging.error(" Lỗi cập nhật: FullName bị trống.")
                 return redirect(url_for("get_employees"))


            # Chuyển đổi DateOfBirth 
            DateOfBirth = None
            if DateOfBirth_str:
                 try:
                    DateOfBirth = datetime.strptime(DateOfBirth_str, '%Y-%m-%d').date()
                 except ValueError:
                     logging.error(f" Lỗi cập nhật: Định dạng ngày sinh không hợp lệ: {DateOfBirth_str}")
                     return redirect(url_for("get_employees"))

            if not DateOfBirth:
                 logging.error(" Lỗi cập nhật: Ngày sinh bị trống hoặc không hợp lệ sau chuyển đổi.")
                 return redirect(url_for("get_employees"))


            # Chuyển đổi DepartmentID và PositionID
            DepartmentID = None
            if DepartmentID_str:
                try:
                    DepartmentID = int(DepartmentID_str)
                except ValueError:
                    logging.warning(f"Cập nhật: DepartmentID không hợp lệ '{DepartmentID_str}', sẽ không cập nhật cột này.")
                    DepartmentID = 'INVALID' 

            PositionID = None
            if PositionID_str:
                try:
                    PositionID = int(PositionID_str)
                except ValueError:
                    logging.warning(f"Cập nhật: PositionID không hợp lệ '{PositionID_str}', sẽ không cập nhật cột này.")
                    PositionID = 'INVALID'


            # Các trường chuỗi có thể là rỗng, gán None nếu rỗng
            Gender = Gender if Gender else None
            PhoneNumber = PhoneNumber if PhoneNumber else None
            Email = Email if Email else None
            Status = Status if Status else None


            # Tìm nhân viên trong hai hệ thống 
            logging.debug(f"Đang tìm nhân viên với ID: {employee_id} để cập nhật.")
            nhan_vien_sql = db.session.query(Employees).filter_by(EmployeeID=employee_id).first()
            nhan_vien_mysql = db.session.query(employees).filter_by(EmployeeID=employee_id).first()

            # Kiểm tra xem nhân viên có tồn tại trong ít nhất một DB không
            if not nhan_vien_sql and not nhan_vien_mysql:
                logging.error(f" Lỗi cập nhật: Không tìm thấy nhân viên với ID {employee_id} trong cả hai CSDL.")
                return redirect(url_for("get_employees"))


            # Cập nhật thông tin nhân viên SQL Server nếu tìm thấy 
            if nhan_vien_sql:
                logging.debug(f"Đang cập nhật dữ liệu SQL Server cho ID {employee_id}")
                # Cập nhật FullName
                nhan_vien_sql.FullName = FullName
                # Cập nhật DateOfBirth
                nhan_vien_sql.DateOfBirth = DateOfBirth 
                nhan_vien_sql.Gender = Gender
                nhan_vien_sql.PhoneNumber = PhoneNumber
                nhan_vien_sql.Email = Email
                nhan_vien_sql.Status = Status
                if DepartmentID != 'INVALID':
                     nhan_vien_sql.DepartmentID = DepartmentID 
                if PositionID != 'INVALID':
                     nhan_vien_sql.PositionID = PositionID     


            # Cập nhật thông tin trong MySQL nếu tìm thấy 
            if nhan_vien_mysql:
                logging.debug(f"Đang cập nhật dữ liệu MySQL cho ID {employee_id}")
                 # Cập nhật FullName (bắt buộc, đã kiểm tra rỗng ở trên)
                nhan_vien_mysql.FullName = FullName
                if DepartmentID != 'INVALID':
                    nhan_vien_mysql.DepartmentID = DepartmentID 
                if PositionID != 'INVALID':
                    nhan_vien_mysql.PositionID = PositionID 
                nhan_vien_mysql.Status = Status 


            # Commit thay đổi 
            logging.debug("Đang cố gắng commit cập nhật...")
            db.session.commit()
            logging.debug(f" Cập nhật nhân viên {employee_id} thành công!")

        except Exception as e: # Bắt lỗi trong quá trình xử lý
            db.session.rollback()
            logging.error(f" LỖI KHI CẬP NHẬT NHÂN VIÊN (ID {employee_id_str if employee_id_str else 'N/A'}): {e}", exc_info=True)
            return f"Đã xảy ra lỗi khi cập nhật nhân viên: {e}", 500

    # Chuyển hướng trở lại trang danh sách nhân viên sau khi xử lý
    logging.debug("Chuyển hướng về /employees sau cập nhật.")
    return redirect(url_for("get_employees"))


# -------------------- ROUTE: XÓA THÔNG TIN NHÂN VIÊN --------------------

# Route để xử lý việc xóa nhân viên. Nhận EmployeeID từ URL.
@app.route("/delete-employee/<int:manv>", methods=["DELETE"])
@authorize(allowed_roles=[UserRole.HR_MANAGER.value, UserRole.ADMIN.value])
def delete_employee(manv): # Nhận ID nhân viên từ URL
    logging.debug(f"### Bắt đầu xử lý request DELETE đến /delete-employee/{manv} ###")
    try:
        # Kiểm tra nếu nhân viên còn liên kết với bảng salaries 
        logging.debug(f"Kiểm tra dữ liệu lương cho nhân viên ID: {manv}")
        luong_ton_tai = salary.query.filter_by(EmployeeID=manv).first()
        if luong_ton_tai:
            logging.warning(f" Không thể xóa nhân viên {manv}: còn dữ liệu lương.")
            return jsonify({"error": f"Không thể xóa nhân viên {manv} vì đang có dữ liệu lương liên kết."}), 400

        logging.debug(f"Kiểm tra dữ liệu chấm công cho nhân viên ID: {manv}")

        cham_cong_ton_tai = Attendance.query.filter_by(EmployeeID=manv).first()

        if cham_cong_ton_tai:
            logging.warning(f" Không thể xóa nhân viên {manv}: còn dữ liệu chấm công.")
             # Trả về phản hồi lỗi
            return jsonify({"error": f"Không thể xóa nhân viên {manv} vì đang có dữ liệu chấm công liên kết."}), 400

        # Tìm nhân viên trong hai hệ thống
        logging.debug(f"Tìm nhân viên ID {manv} trong SQL Server và MySQL.")
        nv_sql = Employees.query.filter_by(EmployeeID=manv).first()
        nv_mysql = employees.query.filter_by(EmployeeID=manv).first()

        if not nv_sql and not nv_mysql:
            logging.warning(f" Không tìm thấy nhân viên với ID {manv} để xóa.")
            return jsonify({"error": f"Nhân viên {manv} không tồn tại trong hệ thống."}), 404

        # Xóa nhân viên ở SQL Server nếu tìm thấy
        if nv_sql:
            db.session.delete(nv_sql)
            logging.debug(f"Đã đánh dấu xóa nhân viên {manv} khỏi SQL Server.")

        # Xóa nhân viên ở MySQL nếu tìm thấy
        if nv_mysql:
            db.session.delete(nv_mysql)
            logging.debug(f"Đã đánh dấu xóa nhân viên {manv} khỏi MySQL.")

        logging.debug("Đang cố gắng commit xóa...")
        db.session.commit()
        logging.debug(f" Đã xóa nhân viên {manv} thành công.")

        # Trả về phản hồi thành công
        return jsonify({"message": f"Đã xóa nhân viên {manv} thành công."}), 200

    except Exception as e: # Bắt lỗi chung trong quá trình xóa
        db.session.rollback()
        logging.error(f" LỖI KHI XÓA NHÂN VIÊN {manv}: {e}", exc_info=True)
        return jsonify({"error": f"Đã xảy ra lỗi khi xóa nhân viên {manv}: {e}"}), 500 # Trả về lỗi server


# -------------------- ROUTE: LẤY DỮ LIỆU CHẤM CÔNG --------------------
@app.route("/attendance", methods=["GET"])
def get_attendance():
    try:
        # Lấy toàn bộ dữ liệu chấm công từ bảng attendance
        attendance_list = Attendance.query.all()

        # Chuyển đổi thành danh sách dictionary
        data = []
        for att in attendance_list:

            data.append({
                "AttendanceID": att.AttendanceID,
                "EmployeeID": att.EmployeeID,
                "WorkDays": att.WorkDays,
                "AbsentDays": att.AbsentDays, 
                "LeaveDays": att.LeaveDays, 
                "AttendanceMonth": att.AttendanceMonth.strftime("%Y-%m-%d") if att.AttendanceMonth else None,
                "CreatedAt": att.CreatedAt 
            })

        return jsonify(data), 200

    except Exception as e:
        logging.error(f" Lỗi khi lấy dữ liệu chấm công: {e}", exc_info=True)
        return jsonify({"error": f"Đã xảy ra lỗi khi lấy dữ liệu chấm công: {e}"}), 500


# -------------------- ROUTE: BÁO CÁO NHÂN SỰ (Đã chỉnh sửa) --------------------

@app.route("/reports", methods=["GET"])
@authorize(allowed_roles=[UserRole.PAYROLL_MANAGER.value, UserRole.ADMIN.value, UserRole.HR_MANAGER.value]) 
def get_reports_data(): 
    try:
        logging.debug("### Bắt đầu lấy dữ liệu báo cáo ###")

        # Dữ liệu tổng quan
        logging.debug("Lấy dữ liệu tổng quan...")
        # Truy vấn dữ liệu tổng số nhân viên theo phòng ban
        by_department = db.session.query(
            Department.DepartmentName, # Lấy tên phòng ban
            func.count(Employees.EmployeeID).label("total")
        ).join(Department, Employees.DepartmentID == Department.DepartmentID).group_by(Department.DepartmentName).all()

        # Truy vấn dữ liệu tổng số nhân viên theo vị trí 
        by_position = db.session.query(
            Position.PositionName, # Lấy tên vị trí
            func.count(Employees.EmployeeID).label("total")
        ).join(Position, Employees.PositionID == Position.PositionID).group_by(Position.PositionName).all()

        # Truy vấn dữ liệu tổng số nhân viên theo giới tính
        by_gender = db.session.query(
            Employees.Gender,
            func.count(Employees.EmployeeID).label("total")
        ).group_by(Employees.Gender).all()

        # Truy vấn dữ liệu tổng số nhân viên theo trạng thái
        by_status = db.session.query(
            Employees.Status,
            func.count(Employees.EmployeeID).label("total")
        ).group_by(Employees.Status).all()

        # Tổng số nhân viên
        total_employees = db.session.query(func.count(Employees.EmployeeID)).scalar() or 0


        total_net_salary_sum = db.session.query(func.sum(salary.NetSalary)).scalar() or 0


        summary_data = {
            "total_employees": total_employees,
            "total_net_salary_sum": total_net_salary_sum,
            "by_department": [{"name": d[0], "total": d[1]} for d in by_department],
            "by_position": [{"name": p[0], "total": p[1]} for p in by_position],
            "by_gender": [{"name": g[0] or "Unknown", "total": g[1]} for g in by_gender], # Xử lý Gender NULL
            "by_status": [{"name": s[0] or "Unknown", "total": s[1]} for s in by_status], # Xử lý Status NULL
        }
        logging.debug(f"Dữ liệu tổng quan: {summary_data}")


        # Dữ liệu bảng lương chi tiết
        logging.debug("Lấy dữ liệu bảng lương chi tiết...")
        # Lấy tất cả bản ghi lương và join với nhân viên để lấy tên
        detailed_payrolls = db.session.query(
            salary.SalaryID,
            salary.EmployeeID,
            Employees.FullName,
            salary.SalaryMonth,
            salary.BaseSalary,
            salary.Bonus,
            salary.Deductions,
            salary.NetSalary
        ).join(Employees, salary.EmployeeID == Employees.EmployeeID).order_by(desc(salary.SalaryMonth), Employees.FullName).all()

        detailed_payroll_data = [{
            "SalaryID": p.SalaryID,
            "EmployeeID": p.EmployeeID,
            "FullName": p.FullName,
            "SalaryMonth": p.SalaryMonth.strftime('%Y-%m-%d') if p.SalaryMonth else None,
            "BaseSalary": p.BaseSalary,
            "Bonus": p.Bonus,
            "Deductions": p.Deductions,
            "NetSalary": p.NetSalary,
        } for p in detailed_payrolls]
        logging.debug(f"Đã lấy {len(detailed_payroll_data)} bản ghi bảng lương chi tiết.")


        # Dữ liệu cho biểu đồ thống kê theo thời gian
        logging.debug("Lấy dữ liệu cho biểu đồ thống kê theo thời gian...")
        # Tổng lương ròng theo tháng
        monthly_salary_trend = db.session.query(
            func.DATE_FORMAT(salary.SalaryMonth, '%Y-%m').label('month'), # Nhóm theo năm-tháng
            func.sum(salary.NetSalary).label('total_net_salary')
        ).filter(salary.SalaryMonth is not None).group_by('month').order_by('month').all()

        monthly_salary_data = [{
            "month": m[0],
            "total_net_salary": m[1]
        } for m in monthly_salary_trend]
        logging.debug(f"Đã lấy {len(monthly_salary_data)} điểm dữ liệu cho biểu đồ lương theo tháng.")

        # Trả về tất cả dữ liệu dưới dạng JSON
        reports_data = {
            "summary": summary_data,
            "detailed_payroll": detailed_payroll_data,
            "monthly_salary_trend": monthly_salary_data
        }

        return jsonify(reports_data), 200

    except Exception as e:
        logging.error(f" LỖI KHI LẤY DỮ LIỆU BÁO CÁO: {e}", exc_info=True)
        return jsonify({"error": f"Đã xảy ra lỗi khi lấy dữ liệu báo cáo: {e}"}), 500

# Route để render trang reports.html
@app.route("/reports-page")
@authorize(allowed_roles=[UserRole.PAYROLL_MANAGER.value, UserRole.ADMIN.value, UserRole.HR_MANAGER.value])
def report_page():
    return render_template("reports.html")

# -------------------- ARLERT  --------------------


@app.route('/alert', methods=['GET'])
def notifications():
    try:
        today = datetime.today().date()  # Chỉ lấy phần ngày
        notifications = []

        # Lấy danh sách nhân viên từ cơ sở dữ liệu
        employees = Employees.query.all()

        for emp in employees:
            try:
                hire_date = emp.HireDate.date() if isinstance(emp.HireDate, datetime) else emp.HireDate
                years_worked = today.year - hire_date.year

                for year in range(1, years_worked + 1):
                    anniversary_date = hire_date + relativedelta(years=year)
                    if 0 <= (anniversary_date - today).days <= 30:
                        notifications.append({
                            "type": "work_anniversary",
                            "title": f"Employee {year}-year approaching work anniversary",
                            "employee_id": emp.EmployeeID,
                            "name": emp.FullName,
                            "hire_date": hire_date.strftime("%d/%m/%Y"),
                            "anniversary_date": anniversary_date.strftime("%d/%m/%Y"),
                            "years_worked": year,
                            "style": "blue-bg"
                        })
            except Exception as e:
                logging.error(f"Lỗi khi xử lý nhân viên ID {emp.EmployeeID}: {e}")

        # Render giao diện notification.html và truyền dữ liệu notifications
        return render_template('notification.html', notifications=notifications)

    except Exception as e:
        # Log lỗi để debug
        logging.error(f"Lỗi trong notifications: {e}")
    return render_template('notification.html', error='Đã xảy ra lỗi khi xử lý thông báo.')


# -------------------- TEST CONNECTION --------------------
@app.route('/test-db')
def test_db():
    results = {}

    # Kiểm tra tất cả các bind key đã cấu hình
    for bind_key, conn_str in app.config['SQLALCHEMY_BINDS'].items():
        try:
            engine = db.get_engine(bind=bind_key)
            with engine.connect() as connection:
                connection.execute(text('SELECT 1'))
            results[bind_key] = ' Kết nối thành công'
            logging.info(f"Kết nối DB '{bind_key}' thành công.")
        except Exception as e: # Bắt Exception chung để log lỗi chi tiết hơn
            results[bind_key] = f' Lỗi kết nối: {str(e)}'
            logging.error(f"Lỗi kết nối DB '{bind_key}': {e}", exc_info=True)


    return jsonify(results), 200 # Trả về status 200

# -------------------- CHẠY APP --------------------

if __name__ == '__main__':
    app.run(debug=True, port=5000) # Có thể chỉ định port