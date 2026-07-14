import json
from fastapi import APIRouter, Depends, HTTPException
from ..db import db_cursor
from ..schemas import SwitchReq
from ..auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/integrations")
def get_integrations(user=Depends(get_current_user)):
    with db_cursor() as (_, cur):
        cur.execute("SELECT config_key, config_value FROM system_config WHERE config_key IN ('collector_active','model_active')")
        rows = cur.fetchall()
        data = {r["config_key"]: json.loads(r["config_value"]) if isinstance(r["config_value"], str) else r["config_value"] for r in rows}
        return data

@router.post("/integrations/switch")
def switch_integrations(req: SwitchReq, user=Depends(get_current_user)):
    if req.switch_type not in ("collector", "model"):
        raise HTTPException(status_code=400, detail="switch_type 必须是 collector/model")

    key = "collector_active" if req.switch_type == "collector" else "model_active"
    value = {"name": req.name, "enabled": True}
    if req.endpoint:
        value["endpoint"] = req.endpoint
    if req.version:
        value["version"] = req.version

    with db_cursor() as (_, cur):
        cur.execute("UPDATE system_config SET config_value=%s WHERE config_key=%s", (json.dumps(value, ensure_ascii=False), key))
    return {"ok": True, "key": key, "value": value}