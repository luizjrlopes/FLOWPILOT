from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..auth import current_user, require
from ..db import get_db
from ..domain import parse_workflow
from ..models import User, Workflow
from ..schemas import WorkflowIn
router=APIRouter(prefix="/workflows",tags=["workflows"])
def serial(w): return {"id":w.id,"name":w.name,"version":w.version,"status":w.status,"trigger":w.trigger_mode,"description":w.description,"yaml":w.yaml_text,"executions":w.execution_count}
@router.get("")
def list_workflows(user:User=Depends(require("workflows:read")),db:Session=Depends(get_db)):
    return [serial(w) for w in db.scalars(select(Workflow).order_by(Workflow.name)).all()]
@router.get("/{workflow_id}")
def get_workflow(workflow_id:str,user:User=Depends(require("workflows:read")),db:Session=Depends(get_db)):
    w=db.get(Workflow,workflow_id)
    if not w: raise HTTPException(404); return serial(w)
    return serial(w)
@router.post("")
def create_workflow(body:WorkflowIn,user:User=Depends(require("workflows:write")),db:Session=Depends(get_db)):
    parsed=parse_workflow(body.yaml_text)
    workflow_id=f"WF-{parsed.id.upper().replace('-','_')}"
    if db.get(Workflow,workflow_id): raise HTTPException(409,"Workflow id already exists")
    w=Workflow(id=workflow_id,name=body.name,version=body.version,status=body.status,trigger_mode=body.trigger_mode,description=body.description,yaml_text=body.yaml_text)
    db.add(w);db.commit();return serial(w)
