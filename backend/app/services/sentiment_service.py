import os
os.environ["TRANSFORMERS_NO_TORCHVISION"] = "1"

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_PATH = r"D:\\CODE\\weibo-sentiment-system\\checkpoint-669"
BATCH_SIZE = 32

FALLBACK_LABEL_MAP = {1: "negative", 2: "neutral", 0: "positive"}

_tokenizer = None
_model = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_label_map = None


def _normalize_label(label: str) -> str:
    s = str(label).strip().lower()
    if "pos" in s or "积极" in s or "正" in s:
        return "positive"
    if "neg" in s or "消极" in s or "负" in s:
        return "negative"
    if "neu" in s or "中性" in s:
        return "neutral"
    return "neutral"


def load_model_once():
    global _tokenizer, _model, _label_map
    if _tokenizer is not None and _model is not None:
        return

    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"模型路径不存在: {MODEL_PATH}")

    _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
    _model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, local_files_only=True)
    _model.to(_device)
    _model.eval()

    if hasattr(_model.config, "id2label") and _model.config.id2label:
        _label_map = {int(k): _normalize_label(v) for k, v in _model.config.id2label.items()}
    else:
        _label_map = FALLBACK_LABEL_MAP


def predict_batch(texts: list[str]) -> list[dict]:
    load_model_once()
    if not texts:
        return []

    results = []
    with torch.no_grad():
        for i in range(0, len(texts), BATCH_SIZE):
            batch = [str(x) if x is not None else "" for x in texts[i:i + BATCH_SIZE]]
            inputs = _tokenizer(batch, return_tensors="pt", truncation=True, padding=True, max_length=512)
            inputs = {k: v.to(_device) for k, v in inputs.items()}

            outputs = _model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            confs, pred_ids = torch.max(probs, dim=-1)

            for cid, conf in zip(pred_ids.tolist(), confs.tolist()):
                label = _label_map.get(int(cid), "neutral")
                label = _normalize_label(label)
                results.append({
                    "label": label,
                    "score": round(float(conf), 4)
                })
    return results


def health():
    try:
        load_model_once()
        return {"ok": True, "device": str(_device), "model_path": MODEL_PATH}
    except Exception as e:
        return {"ok": False, "error": str(e)}