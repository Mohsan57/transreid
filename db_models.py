from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key= True, index = True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    password = Column(String, nullable=False)

class reid_video(Base):
    __tablename__ = "reid_videos"

    id = Column(Integer, primary_key=True, index=True)
    video_name = Column(String,nullable=False)
    video_path = Column(String, nullable=False)