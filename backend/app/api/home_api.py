from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from ..auth import get_current_user
from ..db import db_cursor

router = APIRouter(prefix="/api/home", tags=["home"])


@router.get("/dashboard")
def dashboard(user=Depends(get_current_user)):
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    today = now.date()

    with db_cursor() as (_, cur):
        
        cur.execute("SELECT DATABASE() AS db")
        db_name = cur.fetchone()["db"]

        # 概览
        cur.execute("SELECT COUNT(*) c FROM events")
        total_events = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) c FROM weibos")
        total_weibos = cur.fetchone()["c"]

        cur.execute("SELECT COALESCE(MAX(id), 0) m FROM weibos")
        max_weibo_id = cur.fetchone()["m"]

        cur.execute("SELECT COUNT(*) c FROM weibos WHERE DATE(collected_at)=%s", (today,))
        new_today = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) c FROM weibos WHERE collected_at >= %s", (week_ago,))
        new_7d = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) c FROM weibos WHERE sentiment_label='negative'")
        neg_count = cur.fetchone()["c"]

        negative_ratio = round((neg_count / total_weibos * 100), 2) if total_weibos else 0.0

        # 系统状态
        cur.execute("SELECT MAX(created_at) t FROM analysis_history")
        last_analysis = cur.fetchone()["t"]

        cur.execute("SELECT COUNT(*) c FROM analysis_history")
        total_history = cur.fetchone()["c"]

        # 最近分析记录
        cur.execute("""
            SELECT h.id, h.event_id, e.event_name, h.exported_count, h.created_at
            FROM analysis_history h
            LEFT JOIN events e ON e.id = h.event_id
            ORDER BY h.created_at DESC
            LIMIT 5
        """)
        recent_history = cur.fetchall()

    return {
        "debug": {
            "database": db_name,
            "total_weibos": total_weibos,
            "max_weibo_id": max_weibo_id,
            "new_7d": new_7d,
            "negative_count": neg_count
        },
        "overview": {
            "total_events": total_events,
            "total_weibos": total_weibos,
            "max_weibo_id": max_weibo_id,
            "new_today": new_today,
            "new_7d": new_7d,
            "negative_ratio": negative_ratio
        },
        "system_status": {
            "backend": "online",
            "model": "ready",
            "last_analysis_time": str(last_analysis) if last_analysis else "-",
            "history_count": total_history
        },
        "recent_history": recent_history
    }