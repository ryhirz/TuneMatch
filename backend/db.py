"""数据库会话（SQLAlchemy）。

启动时自动建表（首次运行），正式环境可用 Alembic 迁移（backend/alembic/ 已预留）。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from models import Base

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """建表（幂等）。"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 依赖：请求级会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
