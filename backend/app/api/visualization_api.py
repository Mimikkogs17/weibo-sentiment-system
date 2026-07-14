import io
import json
from collections import Counter, defaultdict
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from ..auth import get_current_user
from ..db import db_cursor

router = APIRouter(prefix="/api/visualization", tags=["visualization"])


def _safe(v):
    if pd.isna(v):
        return ""
    return str(v).strip()


def _to_float(v, d=0.0):
    try:
        return float(v)
    except Exception:
        return d


def _to_int(v, d=0):
    try:
        return int(float(v))
    except Exception:
        return d


def _pick(df, names):
    cols = {str(c).strip().replace("\ufeff", ""): c for c in df.columns}
    for n in names:
        if n in cols:
            return cols[n]
    return None


def _norm_sent(x):
    s = _safe(x).lower()
    if s in ("positive", "pos", "0", "label_0") or "positive" in s or "pos" in s:
        return "positive"
    if s in ("negative", "neg", "1", "label_1") or "negative" in s or "neg" in s:
        return "negative"
    return "neutral"


def _norm_gender(x):
    s = _safe(x).lower()
    if s in ("m", "male", "男"):
        return "男"
    if s in ("f", "female", "女"):
        return "女"
    return "未知"


def _parse_time(x):
    s = _safe(x)
    if not s:
        return None
    fmts = [
        "%a %b %d %H:%M:%S %z %Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
    ]
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(s.replace("/", "-")[:19])
    except Exception:
        return None


def _slot10(dt):
    dt2 = dt.replace(minute=(dt.minute // 10) * 10, second=0, microsecond=0)
    return dt2.strftime("%Y-%m-%d %H:%M")


def _wordcloud(texts):
    stop = {"我们", "你们", "他们", "这个", "那个", "以及", "然后", "就是", "因为", "所以", "但是"}
    cnt = Counter()
    min_len, max_len = 2, 8
    punct = ["，", "。", "！", "？", "、", ",", ".", "!", "?", "；", ";", "：", ":", "\n", "\t", "#", "@",
             "（", "）", "(", ")", "[", "]", "【", "】", "“", "”", "\"", "'", "《", "》", "<", ">", "|", "\\", "/"]
    for t in texts:
        s = t
        for p in punct:
            s = s.replace(p, " ")
        for w in s.split():
            w = w.strip()
            if len(w) < min_len or len(w) > max_len or w in stop:
                continue
            cnt[w] += 1
    return [{"name": k, "value": v} for k, v in cnt.most_common(120)]


def _build_payload(rows, event_id, event_name, event_time_range, summary):
    if not rows:
        return {
            "event_id": event_id,
            "event_name": event_name,
            "event_time_range": event_time_range,
            "summary": summary or "暂无数据",
            "hot_points": [],
            "positive_links": [],
            "negative_links": [],
            "wordcloud": [],
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "trend": {"slots": [], "positive": [], "neutral": [], "negative": []},
            "interaction_scatter": {"positive": [], "neutral": [], "negative": []},
            "gender_sentiment": {
                "categories": ["男", "女", "未知"],
                "positive": [0, 0, 0],
                "neutral": [0, 0, 0],
                "negative": [0, 0, 0],
            },
        }

    texts, hot_points = [], []
    pos = neu = neg = 0
    pos_items, neg_items = [], []
    slot_stat = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0})
    gender_stat = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0})

    scatter = {"positive": [], "neutral": [], "negative": []}

    for r in rows:
        txt = _safe(r.get("content"))
        if not txt:
            continue

        sent = _norm_sent(r.get("sentiment_label"))
        url = _safe(r.get("url")) or "#"
        likes = _to_int(r.get("likes"), _to_int(_to_float(r.get("sentiment_score"), 0.0) * 100000))
        comments = _to_int(r.get("comments"), 0)
        pub = r.get("published_at")
        gender = _norm_gender(r.get("gender"))

        texts.append(txt)
        if len(hot_points) < 12:
            hot_points.append(txt[:70])

        item = {"title": txt[:42] + ("..." if len(txt) > 42 else ""), "url": url, "likes": likes}
        if sent == "positive":
            pos += 1
            pos_items.append(item)
        elif sent == "negative":
            neg += 1
            neg_items.append(item)
        else:
            neu += 1

        # 互动散点：x=点赞 y=评论
        scatter[sent].append([likes, comments, txt[:36]])

        # 性别情绪统计
        gender_stat[gender][sent] += 1

        # 趋势
        dt = _parse_time(pub)
        if dt:
            slot_stat[_slot10(dt)][sent] += 1

    slots = sorted(slot_stat.keys())
    trend = {
        "slots": slots,
        "positive": [slot_stat[s]["positive"] for s in slots],
        "neutral": [slot_stat[s]["neutral"] for s in slots],
        "negative": [slot_stat[s]["negative"] for s in slots],
    }

    cats = ["男", "女", "未知"]
    gender_sentiment = {
        "categories": cats,
        "positive": [gender_stat[c]["positive"] for c in cats],
        "neutral": [gender_stat[c]["neutral"] for c in cats],
        "negative": [gender_stat[c]["negative"] for c in cats],
    }

    return {
        "event_id": event_id,
        "event_name": event_name,
        "event_time_range": event_time_range,
        "summary": summary or f"共{len(texts)}条，积极{pos}，中性{neu}，消极{neg}",
        "hot_points": hot_points,
        "positive_links": sorted(pos_items, key=lambda x: x["likes"], reverse=True)[:5],
        "negative_links": sorted(neg_items, key=lambda x: x["likes"], reverse=True)[:5],
        "wordcloud": _wordcloud(texts),
        "sentiment_distribution": {"positive": pos, "neutral": neu, "negative": neg},
        "trend": trend,
        "interaction_scatter": scatter,
        "gender_sentiment": gender_sentiment,
    }


@router.post("/upload_csv")
async def upload_visual_csv(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="请上传CSV文件")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="文件为空")

    df = None
    for enc in ["utf-8-sig", "utf-8", "gbk", "gb2312"]:
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        raise HTTPException(status_code=400, detail="CSV编码无法识别")

    text_col = _pick(df, ["展示内容", "全部内容", "原生内容"])
    sent_col = _pick(df, ["Sentiment"])
    score_col = _pick(df, ["Score"])
    time_col = _pick(df, ["发布时间"])
    link_col = _pick(df, ["微博链接"])
    likes_col = _pick(df, ["点赞数量", "用户累计点赞数"])
    comments_col = _pick(df, ["评论数量", "用户累计评论数"])
    mid_col = _pick(df, ["mid", "f_mid", "mblogid"])
    user_col = _pick(df, ["个人昵称"])
    gender_col = _pick(df, ["用户性别"])

    if not text_col or not sent_col:
        raise HTTPException(status_code=400, detail=f"缺少必要列：文本列+Sentiment。当前列: {list(df.columns)}")

    std = pd.DataFrame()
    std["weibo_id"] = df[mid_col].astype(str) if mid_col else [f"csv_{i}" for i in range(len(df))]
    std["content"] = df[text_col].fillna("").astype(str)
    std["url"] = df[link_col].fillna("").astype(str) if link_col else ""
    std["user_name"] = df[user_col].fillna("").astype(str) if user_col else ""
    std["gender"] = df[gender_col].fillna("").astype(str) if gender_col else ""
    std["published_at"] = df[time_col].fillna("").astype(str) if time_col else ""
    std["sentiment_label"] = df[sent_col].apply(_norm_sent)
    std["sentiment_score"] = df[score_col].apply(_to_float) if score_col else 0.0
    std["likes"] = df[likes_col].apply(_to_int) if likes_col else 0
    std["comments"] = df[comments_col].apply(_to_int) if comments_col else 0
    std = std.sort_values(by="likes", ascending=False, na_position="last")

    event_name = f"{file.filename.rsplit('.', 1)[0]} 情感分析可视化"

    with db_cursor() as (_, cur):
        cur.execute(
            "INSERT INTO events(event_name, summary, risk_level, start_time, end_time) VALUES(%s,%s,%s,NOW(),NOW())",
            (event_name, "由CSV上传生成", "中")
        )
        event_id = cur.lastrowid

        ins = """
            INSERT INTO weibos
            (weibo_id, event_id, content, url, user_name, published_at, collected_at, sentiment_label, sentiment_score)
            VALUES(%s,%s,%s,%s,%s,%s,NOW(),%s,%s)
        """
        for i, r in std.iterrows():
            txt = _safe(r["content"])
            if not txt:
                continue
            try:
                cur.execute(
                    ins,
                    (
                        _safe(r["weibo_id"]) or f"csv_{event_id}_{i}",
                        event_id,
                        txt,
                        _safe(r["url"]),
                        _safe(r["user_name"]),
                        _safe(r["published_at"]) or None,
                        _safe(r["sentiment_label"]),
                        _to_float(r["sentiment_score"], 0.0),
                    ),
                )
            except Exception:
                pass

        pos = int((std["sentiment_label"] == "positive").sum())
        neu = int((std["sentiment_label"] == "neutral").sum())
        neg = int((std["sentiment_label"] == "negative").sum())
        summary = f"本次CSV共{len(std)}条，积极{pos}，中性{neu}，消极{neg}。"
        cur.execute("UPDATE events SET summary=%s WHERE id=%s", (summary, event_id))

        # 快照（包含互动/性别字段，供可视化读取）
        snap_rows = [
            {
                "content": _safe(r["content"]),
                "url": _safe(r["url"]),
                "sentiment_label": _safe(r["sentiment_label"]),
                "sentiment_score": _to_float(r["sentiment_score"], 0.0),
                "published_at": _safe(r["published_at"]),
                "likes": _to_int(r["likes"], 0),
                "comments": _to_int(r["comments"], 0),
                "gender": _safe(r["gender"]),
            }
            for _, r in std.iterrows()
            if _safe(r["content"])
        ]
        cur.execute(
            "INSERT INTO analysis_history(event_id, snapshot_json, exported_count, created_by) VALUES(%s,%s,0,%s)",
            (event_id, json.dumps({"rows": snap_rows}, ensure_ascii=False), 1),
        )

    return {"ok": True, "event_id": event_id, "event_name": event_name, "rows": int(len(std))}


@router.get("/event/{event_id}")
def event_visualization(event_id: int, user=Depends(get_current_user)):
    with db_cursor() as (_, cur):
        cur.execute("SELECT * FROM events WHERE id=%s", (event_id,))
        event = cur.fetchone()
        if not event:
            raise HTTPException(status_code=404, detail="事件不存在")

        event_name = event.get("event_name") or f"事件#{event_id}"
        event_time_range = f"{event.get('start_time') or '-'} ~ {event.get('end_time') or '-'}"
        summary = event.get("summary") or ""

        # 优先快照
        cur.execute(
            "SELECT snapshot_json FROM analysis_history WHERE event_id=%s ORDER BY id DESC LIMIT 1",
            (event_id,)
        )
        snap = cur.fetchone()
        if snap and snap.get("snapshot_json"):
            try:
                payload = json.loads(snap["snapshot_json"]) if isinstance(snap["snapshot_json"], str) else snap["snapshot_json"]
                rows = payload.get("rows", [])
                return _build_payload(rows, event_id, event_name, event_time_range, summary)
            except Exception:
                pass

        # 回退weibos（无性别/评论/点赞时用默认）
        cur.execute("""
            SELECT content, url, sentiment_label, sentiment_score, published_at
            FROM weibos
            WHERE event_id=%s
            ORDER BY collected_at DESC
            LIMIT 5000
        """, (event_id,))
        rows = cur.fetchall()
        rows = [
            {
                "content": r.get("content"),
                "url": r.get("url"),
                "sentiment_label": r.get("sentiment_label"),
                "sentiment_score": r.get("sentiment_score"),
                "published_at": r.get("published_at"),
                "likes": 0,
                "comments": 0,
                "gender": "",
            }
            for r in rows
        ]

    return _build_payload(rows, event_id, event_name, event_time_range, summary)