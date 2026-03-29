"""
Visit Tracking API
访问记录 API
"""
from fastapi import APIRouter, Request
from sqlalchemy import func, and_
from datetime import datetime, date

from src.db.models import VisitLog
from src.core.dependencies import get_connection_manager

router = APIRouter()


def get_db_config():
    """获取数据库配置"""
    from src.config import get_config
    return get_config().get("database", {})


@router.post("/visit")
async def record_visit(request: Request):
    """记录访问"""
    try:
        body = await request.json()
        page = body.get("page", "/")

        # 获取客户端信息
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:255]

        # 获取 session 中的用户ID（如果已登录）
        user_id = request.headers.get("x-user-id", None)

        # 保存到数据库
        config = get_db_config()
        manager = get_connection_manager()
        session = manager.get_session()

        try:
            visit = VisitLog(
                page=page,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent
            )
            session.add(visit)
            session.commit()
            return {"success": True, "message": "Visit recorded"}
        finally:
            session.close()

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/visit/today")
async def get_today_visits():
    """获取今日访问数"""
    try:
        config = get_db_config()
        manager = get_connection_manager()
        session = manager.get_session()

        try:
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())

            count = session.query(func.count(VisitLog.id)).filter(
                and_(
                    VisitLog.created_at >= today_start,
                    VisitLog.created_at <= today_end
                )
            ).scalar()

            return {"success": True, "count": count or 0}
        finally:
            session.close()

    except Exception as e:
        return {"success": False, "error": str(e), "count": 0}


@router.get("/visit/stats")
async def get_visit_stats(days: int = 7):
    """获取访问统计（最近N天）"""
    try:
        config = get_db_config()
        manager = get_connection_manager()
        session = manager.get_session()

        try:
            from datetime import timedelta
            today = date.today()
            start_date = today - timedelta(days=days - 1)
            start_datetime = datetime.combine(start_date, datetime.min.time())

            results = session.query(
                func.date(VisitLog.created_at).label("date"),
                func.count(VisitLog.id).label("count")
            ).filter(
                VisitLog.created_at >= start_datetime
            ).group_by(
                func.date(VisitLog.created_at)
            ).order_by(
                func.date(VisitLog.created_at)
            ).all()

            stats = [{"date": str(r.date), "count": r.count} for r in results]
            return {"success": True, "stats": stats}
        finally:
            session.close()

    except Exception as e:
        return {"success": False, "error": str(e), "stats": []}
