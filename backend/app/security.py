from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from .models import User

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
bearer = HTTPBearer()
def hash_password(value: str): return pwd_context.hash(value)
def verify_password(value: str, hashed: str): return pwd_context.verify(value, hashed)
def create_token(user: User):
    settings = get_settings()
    payload = {'sub': str(user.id), 'role': user.role, 'exp': datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)}
    return jwt.encode(payload, settings.secret_key, algorithm='HS256')
def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    try: user_id = jwt.decode(credentials.credentials, get_settings().secret_key, algorithms=['HS256'])['sub']
    except (JWTError, KeyError): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Sesión inválida o expirada')
    user = db.get(User, user_id)
    if not user or not user.is_active: raise HTTPException(status_code=401, detail='Usuario no disponible')
    return user
def require_roles(*roles):
    def guard(user: User = Depends(current_user)):
        if user.role not in roles: raise HTTPException(status_code=403, detail='No tienes permiso para esta acción')
        return user
    return guard
