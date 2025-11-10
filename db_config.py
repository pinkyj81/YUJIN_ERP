import urllib
from sqlalchemy import create_engine

# 1️⃣ 먼저 connection_string 정의
connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=ms0501.gabiadb.com;"
    "DATABASE=yujin;"
    "UID=yujin;"
    "PWD=yj8630;"  # ← 실제 비밀번호로 바꾸세요
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

# 2️⃣ URL 인코딩
params = urllib.parse.quote_plus(connection_string)

# 3️⃣ SQLAlchemy 엔진 생성
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# 4️⃣ 연결 테스트
if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            print("✅ SQL Server 연결 성공!")
    except Exception as e:
        print("❌ SQL Error:", e)
