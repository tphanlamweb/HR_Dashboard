SQL_SERVER_CONN = "mssql+pyodbc://sa:123456@PHUONTHARO31/HUMAN?driver=ODBC+Driver+17+for+SQL+Server"
MYSQL_CONN = "mysql+pymysql://root:123456@localhost:3306/payroll"
SQL_SERVER_USERCONN = "mssql+pyodbc://sa:123456@PHUONTHARO31/HR_DASHBOARD?driver=ODBC+Driver+17+for+SQL+Server"

# Cấu hình SQLAlchemy
SQLALCHEMY_BINDS = {
    'sqlserver': SQL_SERVER_CONN,
    'mysql': MYSQL_CONN,
    'userdb': SQL_SERVER_USERCONN
}

SQLALCHEMY_TRACK_MODIFICATIONS = False  # Tắt cảnh báo không cần thiết