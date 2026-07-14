import json
from fastapi import APIRouter, Depends, HTTPException
from ..db import db_cursor
from ..schemas import CreateTaskReq
from ..auth import get_current_user
from ..services.integration_service import trigger_real_collector

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.post("/create")
def create_task(req: CreateTaskReq, user=Depends(get_current_user)):
    with db_cursor() as (_, cur):
        cur.execute("SELECT config_value FROM system_config WHERE config_key='collector_active'")
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="未配置采集器")
        collector = json.loads(row["config_value"]) if isinstance(row["config_value"], str) else row["config_value"]
        collector_name = collector.get("name", "unknown")
        endpoint = collector.get("endpoint", "")

        ret = trigger_real_collector(req.task_name, req.keywords, endpoint)

        cur.execute(
            "INSERT INTO crawl_tasks(task_name, keywords, status, collector_name, started_at, created_by) VALUES(%s,%s,%s,%s,NOW(),%s)",
            (req.task_name, req.keywords, "running" if ret.get("ok") else "failed", collector_name, user["uid"])
        )
        task_id = cur.lastrowid
        return {"ok": ret.get("ok"), "task_id": task_id, "external": ret}