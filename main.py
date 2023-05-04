from fastapi import FastAPI
from routers import user,authentication, video_reid, live_camera
import db_models, database
from database import engine

app = FastAPI()

db_models.Base.metadata.create_all(engine)


app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(video_reid.router)
app.include_router(live_camera.router)