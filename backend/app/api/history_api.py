import json
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from ..db import db_cursor
from ..auth import get_current_user
from ..services.export_service import export_excel, export_pdf

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    event_name: str = Query("", description="按事件名模糊搜索"),
    user=Depends(get_current_user)
):
    offset = (page - 1) * page_size
    with db_cursor() as (_, cur):
        if event_name.strip():
            kw = f"%{event_name.strip()}%"
            cur.execute("""
                SELECT COUNT(*) c
                FROM analysis_history h
                JOIN events e ON h.event_id=e.id
                WHERE e.event_name LIKE %s
            """, (kw,))
            total = cur.fetchone()["c"]

            cur.execute("""
                SELECT h.id, h.event_id, e.event_name, h.exported_count, h.created_by, h.created_at
                FROM analysis_history h
                JOIN events e ON h.event_id=e.id
                WHERE e.event_name LIKE %s
                ORDER BY h.created_at DESC
                LIMIT %s OFFSET %s
            """, (kw, page_size, offset))
            rows = cur.fetchall()
        else:
            cur.execute("SELECT COUNT(*) c FROM analysis_history")
            total = cur.fetchone()["c"]

            cur.execute("""
                SELECT h.id, h.event_id, e.event_name, h.exported_count, h.created_by, h.created_at
                FROM analysis_history h
                JOIN events e ON h.event_id=e.id
                ORDER BY h.created_at DESC
                LIMIT %s OFFSET %s
            """, (page_size, offset))
            rows = cur.fetchall()

    return {"total": total, "rows": rows}


@router.get("/{history_id}")
def get_history(history_id: int, user=Depends(get_current_user)):
    with db_cursor() as (_, cur):
        cur.execute("""
            SELECT h.id, h.event_id, e.event_name, h.snapshot_json, h.exported_count, h.created_by, h.created_at
            FROM analysis_history h
            JOIN events e ON h.event_id=e.id
            WHERE h.id=%s
        """, (history_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="历史记录不存在")

    # snapshot_json 反序列化后返回
    try:
        row["snapshot_json"] = json.loads(row["snapshot_json"]) if isinstance(row["snapshot_json"], str) else row["snapshot_json"]
    except Exception:
        pass
    return row


@router.post("/{history_id}/export/excel")
def download_excel(history_id: int, user=Depends(get_current_user)):
    with db_cursor() as (_, cur):
        cur.execute("SELECT snapshot_json FROM analysis_history WHERE id=%s", (history_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="历史记录不存在")

        file_path = export_excel(history_id, row["snapshot_json"])
        cur.execute("UPDATE analysis_history SET exported_count=exported_count+1 WHERE id=%s", (history_id,))

    return FileResponse(
        path=file_path,
        filename=f"history_{history_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/{history_id}/export/pdf")
def download_pdf(history_id: int, user=Depends(get_current_user)):
    with db_cursor() as (_, cur):
        cur.execute("SELECT snapshot_json FROM analysis_history WHERE id=%s", (history_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="历史记录不存在")

        file_path = export_pdf(history_id, row["snapshot_json"])
        cur.execute("UPDATE analysis_history SET exported_count=exported_count+1 WHERE id=%s", (history_id,))

    return FileResponse(
        path=file_path,
        filename=f"history_{history_id}.pdf",
        media_type="application/pdf"
    )