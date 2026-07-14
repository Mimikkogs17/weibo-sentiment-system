from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.auth_api import router as auth_router
from .api.settings_api import router as settings_router
from .api.visualization_api import router as vis_router
from .api.history_api import router as history_router
from .api.tasks_api import router as tasks_router
from .api.analysis_api import router as analysis_router
from .api.home_api import router as home_router


app = FastAPI(title="Weibo Production System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"ok": True}

app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(vis_router)
app.include_router(history_router)
app.include_router(tasks_router)
app.include_router(analysis_router)
app.include_router(home_router)