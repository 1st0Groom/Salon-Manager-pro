from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys

# [중요] 실행 파일(exe)이 되면 자신의 위치를 찾아내는 코드
if getattr(sys, 'frozen', False):
    # exe로 실행될 때 (여기에 DB를 만듭니다)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # VS Code에서 실행될 때
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# DB 파일 경로 설정
DB_PATH = os.path.join(BASE_DIR, "salon.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()