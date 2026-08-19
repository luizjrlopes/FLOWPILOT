from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..auth import require
from ..db import get_db
from ..models import Execution, User, Workflow
router=APIRouter(prefix="/dashboard",tags=["dashboard"])
@router.get("")
def dashboard(user:User=Depends(require("dashboard:read")),db:Session=Depends(get_db)):
    states=dict(db.execute(select(Execution.state,func.count()).group_by(Execution.state)).all())
    return {"executions":sum(states.values()),"waiting_approval":states.get("WAITING_APPROVAL",0),"dlq":states.get("DLQ",0),"completed":states.get("COMPLETED",0),"workflows":db.scalar(select(func.count()).select_from(Workflow)) or 0}
