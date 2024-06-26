from typing import List
from pydantic import BaseModel



class Users(BaseModel):
    name: str
    email: str
    password: str

class reid_videos(BaseModel):
    video_name: str
    video_path: str

class cameras(BaseModel):
    ip: str | None = None
    username: str | None = None
    password: str | None = None

class show_cameras(BaseModel):
    ip: str
    username: str
    password: str
    class Config():
        orm_mode = True

class networks(BaseModel):
    ip: str | None = None
    username: str | None = None
    password: str | None = None

class show_networks(BaseModel):
    ip: str
    username: str
    password: str
    class Config():
        orm_mode = True
    
class errors(BaseModel):
    error_code: str
    error_message: str
    receiver_email: str


class show_errors(BaseModel):
    id: int
    error_code: str
    error_message: str
    receiver_email: str
    time_created: str
    
    class Config():
        orm_mode = True


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