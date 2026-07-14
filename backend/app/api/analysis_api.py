import os
import io
import uuid
import logging
from datetime import datetime
import json

import pandas as pd
import torch
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from werkzeug.utils import secure_filename
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

from ..auth import get_current_user
from ..db import db_cursor

MODEL_PATH = r"D:\\CODE\\weibo-sentiment-system\\checkpoint-669"
BATCH_SIZE = 32
UPLOAD_FOLDER = "uploads"
EXPORT_FOLDER = "exports"
ALLOWED_EXTENSIONS = {"csv"}

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])

tokenizer = None
model = None
sentiment_pipeline = None
device = 0 if torch.cuda.is_available() else -1


class PredictReq(BaseModel):
    text: str


class BatchPredictReq(BaseModel):
    texts: list[str]


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _normalize_label(raw_label: str) -> str:
    s = str(raw_label).strip().lower()
    if s in ("label_0", "0", "positive", "pos"):
        return "positive"
    if s in ("label_1", "1", "negative", "neg"):
        return "negative"
    if s in ("label_2", "2", "neutral", "neu"):
        return "neutral"
    if "pos" in s:
        return "positive"
    if "neg" in s:
        return "negative"
    return "neutral"


def _load_model_once():
    global tokenizer, model, sentiment_pipeline
    if sentiment_pipeline is not None:
        return
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"模型路径不存在: {MODEL_PATH}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, local_files_only=True)
    sentiment_pipeline = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        return_all_scores=True,
        device=device
    )


def _predict_texts(texts: list[str]) -> list[dict]:
    _load_model_once()
    if not texts:
        return []
    clean_texts = [str(t) if t is not None else "" for t in texts]
    all_scores = sentiment_pipeline(clean_texts, truncation=True, max_length=512)

    results = []
    for score_list in all_scores:
        best = max(score_list, key=lambda x: x.get("score", 0.0))
        results.append({
            "label": _normalize_label(best.get("label", "neutral")),
            "score": round(float(best.get("score", 0.0)), 4)
        })
    return results


def _pick_text_column(df: pd.DataFrame, preferred: str | None) -> str | None:
    normalized = {str(c).strip().replace("\ufeff", ""): c for c in df.columns}
    if preferred and preferred.strip():
        p = preferred.strip().replace("\ufeff", "")
        if p in normalized:
            return normalized[p]
    candidates = ["展示内容", "全部内容","text", "内容", "正文", "微博内容", "评论内容", "文案", "句子"]
    for c in candidates:
        if c in normalized:
            return normalized[c]
    for col in df.columns:
        sample = df[col].head(20).fillna("").astype(str)
        if (sample.str.len() > 0).mean() >= 0.6:
            return col
    return None


def _ascii_filename(original: str) -> str:
    stem = os.path.splitext(original or "upload")[0]
    safe = "".join(ch if ch.isalnum() else "_" for ch in stem)
    if not safe:
        safe = "upload"
    return f"predicted_{safe}.csv"


@router.get("/health")
def health():
    try:
        _load_model_once()
        return {"ok": True, "device": "cuda" if device == 0 else "cpu", "model_path": MODEL_PATH}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/predict")
def predict_one(req: PredictReq):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text 不能为空")
    return _predict_texts([text])[0]


@router.post("/predict_batch")
def predict_batch_api(req: BatchPredictReq):
    if not req.texts:
        raise HTTPException(status_code=400, detail="texts 不能为空")
    return {"rows": _predict_texts(req.texts)}


@router.post("/predict_csv")
async def predict_csv(
    file: UploadFile = File(...),
    text_column: str = Form(default="展示内容")
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")
    if not _allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="无效文件类型，仅支持 csv")

    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(EXPORT_FOLDER, exist_ok=True)

        raw_name = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        base, ext = os.path.splitext(raw_name)
        temp_filename = f"{base}_{timestamp}{ext}"
        upload_path = os.path.join(UPLOAD_FOLDER, temp_filename)

        content = await file.read()
        with open(upload_path, "wb") as f:
            f.write(content)

        encodings_to_try = ["utf-8-sig", "utf-8", "gbk", "gb2312"]
        df = None
        encoding_used = "unknown"
        for enc in encodings_to_try:
            try:
                df = pd.read_csv(upload_path, encoding=enc)
                encoding_used = enc
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            raise HTTPException(status_code=400, detail=f"无法解码CSV，尝试编码: {encodings_to_try}")
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV 没有数据行")

        chosen_col = _pick_text_column(df, text_column)
        if not chosen_col:
            raise HTTPException(status_code=400, detail=f"未找到文本列，当前列: {list(df.columns)}")

        texts = df[chosen_col].fillna("").astype(str).tolist()
        preds = _predict_texts(texts)

        df["Sentiment"] = [p["label"] for p in preds]
        df["Score"] = [p["score"] for p in preds]

        out_filename = f"analyzed_{uuid.uuid4().hex[:10]}.csv"
        out_path = os.path.join(EXPORT_FOLDER, out_filename)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")

        pos = sum(1 for p in preds if p["label"] == "positive")
        neu = sum(1 for p in preds if p["label"] == "neutral")
        neg = sum(1 for p in preds if p["label"] == "negative")

        # 所有 header 值必须是 ASCII
        headers = {
            "X-Used-Encoding": encoding_used,
            "X-Stat-Positive": str(pos),
            "X-Stat-Neutral": str(neu),
            "X-Stat-Negative": str(neg),
            "X-Output-File": out_filename
        }

            # 写历史快照（自动）
        # 若系统里没有事件，这里创建一个“CSV导入事件”
        with db_cursor() as (_, cur):
            cur.execute("SELECT id, event_name FROM events ORDER BY id DESC LIMIT 1")
            evt = cur.fetchone()

            if not evt:
                cur.execute("""
                    INSERT INTO events(event_name, summary, risk_level, start_time, end_time)
                    VALUES(%s, %s, %s, NOW(), NOW())
                """, ("CSV导入事件", "由CSV分析自动创建", "中"))
                event_id = cur.lastrowid
                event_name = "CSV导入事件"
            else:
                event_id = evt["id"]
                event_name = evt["event_name"]

            snapshot = {
                "event_name": event_name,
                "summary": {
                    "positive": pos,
                    "neutral": neu,
                    "negative": neg,
                    "total": len(preds)
                },
                "rows": [
                    {
                        "text": texts[i],
                        "Sentiment": preds[i]["label"],
                        "Score": preds[i]["score"]
                    } for i in range(min(len(texts), 1000))
                ]
            }

            cur.execute("""
                INSERT INTO analysis_history(event_id, snapshot_json, exported_count, created_by)
                VALUES(%s, %s, 0, %s)
            """, (event_id, json.dumps(snapshot, ensure_ascii=False), 1))

        return FileResponse(
            path=out_path,
            filename=_ascii_filename(file.filename),  # 仅 ASCII
            media_type="text/csv",
            headers=headers
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("CSV 情感分析失败")
        raise HTTPException(status_code=500, detail=f"分析过程出错: {e}")


@router.post("/run_event/{event_id}")
def run_event_analysis(event_id: int, user=Depends(get_current_user)):
    with db_cursor() as (_, cur):
        cur.execute("SELECT id, content FROM weibos WHERE event_id=%s", (event_id,))
        rows = cur.fetchall()

    if not rows:
        return {"ok": True, "event_id": event_id, "total": 0, "updated": 0}

    ids = [r["id"] for r in rows]
    texts = [r.get("content", "") for r in rows]
    preds = _predict_texts(texts)

    updated = 0
    with db_cursor() as (_, cur):
        for wid, pred in zip(ids, preds):
            cur.execute(
                "UPDATE weibos SET sentiment_label=%s, sentiment_score=%s WHERE id=%s",
                (pred["label"], pred["score"], wid)
            )
            updated += 1

    return {"ok": True, "event_id": event_id, "total": len(rows), "updated": updated}