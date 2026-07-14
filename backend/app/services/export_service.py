import os
import json
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from ..config import EXPORT_DIR


def ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)


def _safe_str(v):
    if v is None:
        return ""
    return str(v).strip()


def _pick(d: dict, keys, default=""):
    for k in keys:
        if k in d and d[k] is not None and str(d[k]).strip() != "":
            return d[k]
    return default


def _norm_sent(v):
    s = _safe_str(v).lower()
    if s in ("positive", "pos", "0", "label_0") or "positive" in s or "pos" in s:
        return "positive"
    if s in ("negative", "neg", "1", "label_1") or "negative" in s or "neg" in s:
        return "negative"
    return "neutral"


def _normalize_rows(rows):
    out = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue

        content = _safe_str(_pick(r, ["content", "text", "展示内容", "全部内容", "原生内容"], ""))
        sentiment = _norm_sent(_pick(r, ["sentiment_label", "Sentiment", "sentiment"], "neutral"))
        score = _pick(r, ["sentiment_score", "Score", "score"], 0)
        published_at = _safe_str(_pick(r, ["published_at", "发布时间"], ""))
        user_name = _safe_str(_pick(r, ["user_name", "个人昵称"], ""))
        url = _safe_str(_pick(r, ["url", "微博链接"], ""))
        likes = _pick(r, ["likes", "点赞数量", "用户累计点赞数"], 0)
        comments = _pick(r, ["comments", "评论数量", "用户累计评论数"], 0)

        if not content:
            continue

        out.append({
            "content": content,
            "sentiment_label": sentiment,
            "sentiment_score": score,
            "published_at": published_at,
            "user_name": user_name,
            "url": url,
            "likes": likes,
            "comments": comments,
        })
    return out


def _compute_summary(rows):
    pos = sum(1 for r in rows if r.get("sentiment_label") == "positive")
    neu = sum(1 for r in rows if r.get("sentiment_label") == "neutral")
    neg = sum(1 for r in rows if r.get("sentiment_label") == "negative")
    return {
        "positive": pos,
        "neutral": neu,
        "negative": neg,
        "total": len(rows),
    }


def _load_data(snapshot_json):
    data = json.loads(snapshot_json) if isinstance(snapshot_json, str) else (snapshot_json or {})
    rows = _normalize_rows(data.get("rows", []))
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    event_name = _safe_str(data.get("event_name", ""))

    # 若summary缺失或不完整，则按rows重算
    if not summary or any(k not in summary for k in ["positive", "neutral", "negative", "total"]):
        summary = _compute_summary(rows)

    return data, rows, summary, event_name


def export_excel(history_id: int, snapshot_json: str) -> str:
    ensure_export_dir()
    _, rows, summary, event_name = _load_data(snapshot_json)

    excel_path = os.path.join(EXPORT_DIR, f"history_{history_id}.xlsx")

    # 统一导出字段，避免原始列名不一致
    export_rows = []
    for r in rows:
        export_rows.append({
            "content": r.get("content", ""),
            "sentiment_label": r.get("sentiment_label", "neutral"),
            "sentiment_score": r.get("sentiment_score", 0),
            "published_at": r.get("published_at", ""),
            "user_name": r.get("user_name", ""),
            "url": r.get("url", ""),
            "likes": r.get("likes", 0),
            "comments": r.get("comments", 0),
        })

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        pd.DataFrame(export_rows).to_excel(writer, index=False, sheet_name="rows")

        summary_rows = [
            {"key": "event_name", "value": event_name},
            {"key": "positive", "value": summary.get("positive", 0)},
            {"key": "neutral", "value": summary.get("neutral", 0)},
            {"key": "negative", "value": summary.get("negative", 0)},
            {"key": "total", "value": summary.get("total", 0)},
        ]
        pd.DataFrame(summary_rows).to_excel(writer, index=False, sheet_name="summary")

    return excel_path


def _register_cjk_font():
    # Windows常见中文字体路径，按顺序尝试
    candidates = [
        ("MicrosoftYaHei", r"C:\Windows\Fonts\msyh.ttc"),
        ("SimSun", r"C:\Windows\Fonts\simsun.ttc"),
        ("SimHei", r"C:\Windows\Fonts\simhei.ttf"),
    ]
    for font_name, font_path in candidates:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                return font_name
            except Exception:
                pass
    return "Helvetica"  # 兜底（无中文支持）


def export_pdf(history_id: int, snapshot_json: str) -> str:
    ensure_export_dir()
    _, rows, summary, event_name = _load_data(snapshot_json)
    rows = rows[:30]  # PDF只展示前30条

    pdf_path = os.path.join(EXPORT_DIR, f"history_{history_id}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)

    font_name = _register_cjk_font()
    c.setFont(font_name, 12)

    y = 800
    c.drawString(40, y, f"History Report #{history_id}")
    y -= 24
    c.drawString(40, y, f"Event: {event_name or '-'}")
    y -= 20
    c.drawString(40, y, f"Positive: {summary.get('positive', 0)}")
    y -= 16
    c.drawString(40, y, f"Neutral : {summary.get('neutral', 0)}")
    y -= 16
    c.drawString(40, y, f"Negative: {summary.get('negative', 0)}")
    y -= 16
    c.drawString(40, y, f"Total   : {summary.get('total', 0)}")
    y -= 24
    c.drawString(40, y, "Samples:")
    y -= 18

    if not rows:
        c.drawString(40, y, "No rows in snapshot.")
        c.save()
        return pdf_path

    for i, r in enumerate(rows, 1):
        sent = _safe_str(r.get("sentiment_label", "neutral"))
        txt = _safe_str(r.get("content", ""))[:80]
        line = f"{i}. [{sent}] {txt}"
        c.drawString(40, y, line)
        y -= 16
        if y < 60:
            c.showPage()
            c.setFont(font_name, 12)
            y = 800

    c.save()
    return pdf_path