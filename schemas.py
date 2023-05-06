from typing import List
from pydantic import BaseModel



class Users(BaseModel):
    name: str
    email: str
    password: str

class reid_videos(BaseModel):
    video_name: str
    video_path: str

class show_reid_videos(reid_videos):
    pass

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