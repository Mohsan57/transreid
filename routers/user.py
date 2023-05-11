from fastapi import APIRouter, Depends, status, Response, HTTPException
from typing import List
import schemas, db_models
from sqlalchemy.orm import Session
from database import get_db
from fastapi.security import OAuth2PasswordRequestForm
import OAuth
import os

from controller import userController

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post("/", response_model=schemas.Show_User, status_code=status.HTTP_201_CREATED)
def Create_user(request:schemas.Users, db: Session = Depends(get_db)):
    
    if (request.email.strip() != "" and request.name.strip() != "" and request.password.strip() != ""):
        return userController.add_new_user(db=db, name=request.name, email= request.email, password= request.password)
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Enter All Details")
   
    
    

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_data(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends(OAuth.get_current_user)):
    user = userController.show_user_data(db,form_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not Found")
    return user
