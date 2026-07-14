def trigger_real_collector(task_name: str, keywords: str, collector_endpoint: str):
    # TODO: 调用真实采集系统（HTTP/RPC/消息队列）
    # 返回任务ID或状态
    return {"ok": True, "external_task_id": f"TASK-{task_name}"}

def analyze_with_real_model(texts: list[str], model_name: str):
    # TODO: 调用真实情感模型，返回 label/score
    # 示例返回格式
    result = []
    for t in texts:
        result.append({"label": "neutral", "score": 0.0})
    return result