from fastapi import FastAPI
from routers import user,authentication, video_reid, live_camera
import db_models, database
from database import engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

db_models.Base.metadata.create_all(engine)
origins = [
       "http://localhost",
       "http://localhost:3000",]

app.add_middleware(
       CORSMiddleware,
       allow_origins=origins,
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )



app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(video_reid.router)
app.include_router(live_camera.router)