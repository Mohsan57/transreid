from fastapi import APIRouter, Depends, status, HTTPException
import schemas, database, db_models
from hashing import hash
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import JWTToken
from jose import JWTError, jwt

router = APIRouter(
    tags=["Authentication"]
)

@router.post("/login", status_code= status.HTTP_200_OK)
async def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    print(request.username)
    user = db.query(db_models.User).filter(db_models.User.email == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid email or password")
    if not hash.verify_password(request.password,user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid email or password")
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = JWTToken.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

