from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from ..audit import record
from ..auth import require
from ..db import get_db
from ..domain import can_decide
from ..messaging import publish_run
from ..models import Approval, Execution, ExecutionEvent, User
from ..schemas import DecisionIn
router=APIRouter(prefix="/approvals",tags=["approvals"])
@router.get("")
def pending(user:User=Depends(require("approvals:read")),db:Session=Depends(get_db)):
    runs=db.scalars(select(Execution).where(Execution.state=="WAITING_APPROVAL").order_by(Execution.created_at)).all()
    return [{"id":r.id,"workflow_id":r.workflow_id,"input":r.input_json,"ai":r.ai_json,"created_at":r.created_at} for r in runs]
@router.post("/{run_id}")
def decide(run_id:str,body:DecisionIn,user:User=Depends(require("approvals:decide")),db:Session=Depends(get_db)):
    r=db.get(Execution,run_id)
    if not r or not can_decide(r.state): raise HTTPException(409,"Run is not waiting for approval")
    if body.decision=="reject" and not body.reason.strip(): raise HTTPException(422,"Rejection reason is required")
    ap=Approval(execution_id=r.id,decision=body.decision,reason=body.reason,decided_by=user.name);db.add(ap)
    if body.decision=="approve":
        r.state="APPROVED";db.add(ExecutionEvent(execution_id=r.id,type="APPROVAL_GRANTED",detail=f"Aprovado por {user.name}: {body.reason or 'sem observações'}"));action="APPROVAL_GRANTED"
    else:
        r.state="REJECTED";db.add(ExecutionEvent(execution_id=r.id,type="APPROVAL_REJECTED",detail=f"Rejeitado por {user.name}: {body.reason}",level="failed"));action="APPROVAL_REJECTED"
    record(db,actor=user.name,action=action,entity_type="RUN",entity_id=r.id,details=body.reason or body.decision);db.commit()
    if body.decision=="approve": publish_run(r.id,"resume")
    return {"run_id":r.id,"state":r.state}
