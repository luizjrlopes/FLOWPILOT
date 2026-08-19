from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import admin, approvals, auth, dashboard, executions, workflows
app=FastAPI(title="FlowPilot API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
for r in [auth.router,dashboard.router,workflows.router,executions.router,approvals.router,admin.router]: app.include_router(r)
@app.get("/health")
def health(): return {"status":"ok"}
