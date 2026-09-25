"""用户反馈路由：个性化学习数据"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from models import UserFeedback
from schemas import ok

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("/reset")
def reset_feedback(db: Session = Depends(get_db)) -> dict:
    """清空所有反馈数据（重置个性化偏好）。"""
    try:
        db.query(UserFeedback).delete()
        db.commit()
        return ok({"deleted": True}, message="已清空反馈数据,偏好已重置")
    except Exception as e:
        db.rollback()
        return ok({"deleted": False, "error": str(e)})
