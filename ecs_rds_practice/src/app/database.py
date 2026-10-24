import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "postgres")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy engine & session
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(retries=2, delay=1):
    """Tự động kết nối và khởi tạo bảng dữ liệu với retry logic."""
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Đang kết nối tới PostgreSQL ({DB_HOST}:{DB_PORT}/{DB_NAME}) - Thử lần {attempt}/{retries}...")
            # Import models to register metadata
            from app import models
            Base.metadata.create_all(bind=engine)
            logger.info("Kết nối database và tạo bảng thành công!")
            return True
        except Exception as e:
            logger.warning(f"Chưa kết nối được DB (lần {attempt}): {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                logger.error("Chưa thể kết nối tới database lúc khởi động. Ứng dụng vẫn tiếp tục chạy.")
                return False
