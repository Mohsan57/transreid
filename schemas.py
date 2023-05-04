from typing import List
from pydantic import BaseModel



class Users(BaseModel):
    name: str
    email: str
    password: str


class Show_User(BaseModel):
    id: int
    name: str
    email: str
    
    class Config():
        orm_mode = True



class login(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None