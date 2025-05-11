from extension import db

# Bảng Users trong cơ sở dữ liệu HR_DASHBOARD
class Users(db.Model):
    __tablename__ = 'Users'
    __bind_key__ = 'userdb' # Sử dụng kết nối SQL_SERVER_USERCONN
    Users_ID = db.Column(db.Integer, primary_key=True)
    User_Name = db.Column(db.String(50), nullable=False)
    User_Role = db.Column(db.Integer, nullable=False)
    User_Password = db.Column(db.String(50), nullable=False)

# Bảng Employees trong cơ sở dữ liệu HUMAN(SQL Server)
class Employees(db.Model):
    __tablename__ = 'Employees'
    __bind_key__ = 'sqlserver'  # Sử dụng kết nối SQL_SERVER_CONN
    EmployeeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FullName = db.Column(db.String(100), nullable=False)
    DateOfBirth = db.Column(db.Date, nullable=False)
    Gender = db.Column(db.String(10))
    PhoneNumber = db.Column(db.String(15))
    Email = db.Column(db.String(100))
    HireDate = db.Column(db.Date, nullable=False)
    DepartmentID = db.Column(db.Integer)
    PositionID = db.Column(db.Integer)
    Status = db.Column(db.String(50))

# Bảng Employees trong cơ sở dữ liệu PAYROLL (MySQL)
class employees(db.Model):
    __tablename__ = 'employees'
    __bind_key__ = 'mysql'  # Sử dụng kết nối MYSQL_CONN
    EmployeeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FullName = db.Column(db.String(100), nullable=False)
    DepartmentID = db.Column(db.Integer)
    PositionID = db.Column(db.Integer)
    Status = db.Column(db.String(50))

# Bảng Salaries trong cơ sở dữ liệu PAYROLL (MySQL)
class salaries(db.Model):
    __tablename__ = 'salaries'
    __bind_key__ = 'mysql'  # Sử dụng kết nối MYSQL_CONN
    SalaryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.Integer, db.ForeignKey("employees.EmployeeID"))
    SalaryMonth = db.Column(db.Date)
    BaseSalary = db.Column(db.Float)
    Bonus = db.Column(db.Float)
    Deductions = db.Column(db.Float)
    NetSalary = db.Column(db.Float)

# Bảng Attendance trong cơ sở dữ liệu PAYROLL (MySQL)
class attendance(db.Model):
    __tablename__ = 'attendance'
    __bind_key__ = 'mysql'  # Sử dụng kết nối MYSQL_CONN
    AttendanceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.Integer, db.ForeignKey("employees.EmployeeID"))
    WorkDays = db.Column(db.Integer)
    AbsentDay = db.Column(db.Integer)
    LeavesDay = db.Column(db.Integer)
    AttendanceMon = db.Column(db.Date)