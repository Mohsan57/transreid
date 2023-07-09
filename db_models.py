from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from typing import List
from sqlalchemy.orm import Mapped


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key= True, index = True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    password = Column(String, nullable=False)
    
    reid_video: Mapped[List["Reid_Video"]] = relationship(back_populates = "user")
    camera: Mapped[List['Camera']] = relationship(back_populates="user")
    network: Mapped[List['Network']] = relationship(back_populates="user")
    

class Reid_Video(Base):
    __tablename__ = "reid_videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_name = Column(String,nullable=False)
    video_path = Column(String, nullable=False)
    img_name = Column(String,nullable=False)
    img_path = Column(String, nullable=False)   
    user = relationship("User", back_populates="reid_video")
    
class Error(Base):
    __tablename__ = "errors"

    id = Column(Integer, primary_key=True, index=True)
    error_code = Column(String,nullable=True)
    error_message = Column(String, nullable=True)
    receiver_email = Column(String,nullable=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    
class Camera(Base):
    __tablename__ = 'cameras'
    
    id = Column(Integer,primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip = Column(String, unique=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
        
    
    user = relationship("User",back_populates="camera")

class Network(Base):
    __tablename__ = 'networks'
    
    id = Column(Integer,primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip = Column(String, unique=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    
    user = relationship("User",back_populates="network")
    