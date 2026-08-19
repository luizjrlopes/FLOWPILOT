from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from ..audit import record
from ..auth import require
from ..db import get_db
from ..domain import can_reprocess
from ..messaging import publish_run
from ..models import Execution, ExecutionEvent, User, WebhookReceipt, Workflow, uid
from ..schemas import TriggerIn
router=APIRouter(tags=["executions"])
def serialize(r): return {"id":r.id,"workflow_id":r.workflow_id,"state":r.state,"trigger":r.trigger,"actor":r.actor_name,"input":r.input_json,"ai":r.ai_json,"result":r.result_json,"current_step":r.current_step,"retry":r.retry_count,"parent_run_id":r.parent_run_id,"error":r.error,"created_at":r.created_at,"updated_at":r.updated_at,"events":[{"id":e.id,"type":e.type,"detail":e.detail,"level":e.level,"metadata":e.metadata_json,"created_at":e.created_at} for e in r.events]}
def full_stmt(): return select(Execution).options(selectinload(Execution.events)).order_by(Execution.created_at.desc())
@router.get("/executions")
def list_runs(user:User=Depends(require("executions:read")),db:Session=Depends(get_db)):
    return [serialize(r) for r in db.scalars(full_stmt()).all()]
@router.get("/executions/{run_id}")
def get_run(run_id:str,user:User=Depends(require("executions:read")),db:Session=Depends(get_db)):
    r=db.scalar(full_stmt().where(Execution.id==run_id))
    if not r: raise HTTPException(404); return serialize(r)
    return serialize(r)
def new_run(db,workflow_id,body,trigger,actor,parent=None):
    w=db.get(Workflow,workflow_id)
    if not w or w.status!="Ativo": raise HTTPException(404,"Active workflow not found")
    r=Execution(id=uid("RUN"),workflow_id=workflow_id,state="QUEUED",trigger=trigger,actor_name=actor,input_json=body.model_dump(),parent_run_id=parent)
    r.events.append(ExecutionEvent(type="TRIGGER_RECEIVED",detail=f"{trigger} trigger accepted by {actor}"));w.execution_count+=1;db.add(r);return r
@router.post("/workflows/{workflow_id}/runs")
def trigger(workflow_id:str,body:TriggerIn,user:User=Depends(require("executions:trigger")),db:Session=Depends(get_db)):
    r=new_run(db,workflow_id,body,"manual",user.name);record(db,actor=user.name,action="RUN_TRIGGERED",entity_type="RUN",entity_id=r.id,details=f"workflow={workflow_id}");db.commit();publish_run(r.id);return {"run_id":r.id,"state":r.state}
@router.post("/hooks/supplier")
def webhook(body:TriggerIn,x_idempotency_key:str=Header(...),db:Session=Depends(get_db)):
    prior=db.scalar(select(WebhookReceipt).where(WebhookReceipt.idempotency_key==x_idempotency_key))
    if prior: return {"run_id":prior.execution_id,"duplicate":True}
    r=new_run(db,"WF-SUPPLIER-ONBOARDING",body,"webhook","Webhook");db.flush();db.add(WebhookReceipt(idempotency_key=x_idempotency_key,execution_id=r.id));record(db,actor="Webhook",action="WEBHOOK_ACCEPTED",entity_type="RUN",entity_id=r.id,details="idempotency key accepted");db.commit();publish_run(r.id);return {"run_id":r.id,"duplicate":False}
@router.post("/executions/{run_id}/reprocess")
def reprocess(run_id:str,user:User=Depends(require("dlq:retry")),db:Session=Depends(get_db)):
    original=db.get(Execution,run_id)
    if not original or not can_reprocess(original.state): raise HTTPException(409,"Only DLQ runs can be reprocessed")
    body=TriggerIn.model_validate(original.input_json);r=new_run(db,original.workflow_id,body,"dlq-reprocess",user.name,parent=original.id);record(db,actor=user.name,action="DLQ_REPROCESSED",entity_type="RUN",entity_id=r.id,details=f"parent={original.id}");db.commit();publish_run(r.id);return {"run_id":r.id,"parent_run_id":original.id}
