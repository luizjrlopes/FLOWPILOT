from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .domain import can
from .models import User

bearer = HTTPBearer(auto_error=False)

def issue_token(user: User) -> str:
    payload = {"sub": user.id, "name": user.name, "role": user.role, "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_ttl_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials: raise HTTPException(401, "Authentication required")
    try: payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError: raise HTTPException(401, "Invalid session")
    user = db.get(User, payload.get("sub"))
    if not user: raise HTTPException(401, "Unknown user")
    return user

def require(permission: str):
    def dep(user: User = Depends(current_user)):
        if not can(user.role, permission): raise HTTPException(403, f"Missing permission: {permission}")
        return user
    return dep
