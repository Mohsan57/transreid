from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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

class errors(Base):
    __tablename__ = "errors"

    id = Column(Integer, primary_key=True, index=True)
    error_code = Column(String,nullable=True)
    error_message = Column(String, nullable=True)
    receiver_email = Column(String,nullable=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())