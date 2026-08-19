from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..auth import issue_token
from ..db import get_db
from ..models import User
from ..schemas import LoginIn
router=APIRouter(prefix="/auth",tags=["auth"])
@router.get("/demo-users")
def users(db:Session=Depends(get_db)):
    return [{"id":u.id,"name":u.name,"role":u.role} for u in db.scalars(select(User).order_by(User.name)).all()]
@router.post("/demo-login")
def login(body:LoginIn,db:Session=Depends(get_db)):
    user=db.get(User,body.user_id)
    if not user: raise HTTPException(404,"User not found")
    return {"token":issue_token(user),"user":{"id":user.id,"name":user.name,"role":user.role}}
