from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..audit import record
from ..auth import require
from ..db import get_db
from ..models import AuditEvent, Connector, SystemFlag, User
from ..schemas import FlagIn
from ..seed import reset_demo
router=APIRouter(tags=["admin"])
@router.get("/connectors")
def connectors(user:User=Depends(require("connectors:read")),db:Session=Depends(get_db)):
    flags={x.key:x.enabled for x in db.scalars(select(SystemFlag)).all()}
    return {"items":[{"id":c.id,"name":c.name,"kind":c.kind,"status":c.status,"calls":c.calls,"failures":c.failures} for c in db.scalars(select(Connector)).all()],"flags":flags}
@router.put("/flags/{key}")
def set_flag(key:str,body:FlagIn,user:User=Depends(require("connectors:write")),db:Session=Depends(get_db)):
    item=db.get(SystemFlag,key)
    if not item: raise HTTPException(404)
    item.enabled=body.enabled;record(db,actor=user.name,action="SYSTEM_FLAG_CHANGED",entity_type="FLAG",entity_id=key,details=f"enabled={body.enabled}");db.commit();return {"key":key,"enabled":item.enabled}
@router.get("/audit")
def audit(user:User=Depends(require("audit:read")),db:Session=Depends(get_db)):
    rows=db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200)).all()
    return [{"id":a.id,"at":a.created_at,"actor":a.actor,"action":a.action,"entity_type":a.entity_type,"entity_id":a.entity_id,"details":a.details,"metadata":a.metadata_json} for a in rows]
@router.post("/demo/reset")
def reset(user:User=Depends(require("demo:reset")),db:Session=Depends(get_db)):
    reset_demo(db);return {"ok":True}
