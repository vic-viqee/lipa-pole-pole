from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.vendor import Vendor

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_vendor(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Vendor:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
    vendor = db.query(Vendor).filter(Vendor.id == int(payload["sub"])).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return vendor