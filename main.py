from fastapi import FastAPI,HTTPException, BackgroundTasks, Request
from typing import List
from routers import user,authentication, video_reid, live_camera, arduino_test, sync_camera_network
import db_models, database
from database import engine
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from setting import ORIGINS
# for Ngrok
# from fastapi.logger import logger
# from pydantic import BaseSettings
# import os
# import sys


# class Settings(BaseSettings):
#     # ... The rest of our FastAPI settings

#     BASE_URL = "http://localhost:8000"
#     USE_NGROK = os.environ.get("USE_NGROK", "True") == "True"


# settings = Settings()


# def init_webhooks(base_url):
#     # Update inbound traffic via APIs to use the public-facing ngrok URL
#     pass


app = FastAPI()

#for Ngrok

# if settings.USE_NGROK:
#     # pyngrok should only ever be installed or initialized in a dev environment when this flag is set
#     from pyngrok import ngrok

#     # Get the dev server port (defaults to 8000 for Uvicorn, can be overridden with `--port`
#     # when starting the server
#     port = 8000

#     # Open a ngrok tunnel to the dev server
#     public_url = ngrok.connect(port).public_url
#     logger.info("ngrok tunnel \"{}\" -> \"http://127.0.0.1:{}\"".format(public_url, port))

#     # Update any base URLs or webhooks to use the public ngrok URL
#     settings.BASE_URL = public_url
#     init_webhooks(public_url)
#-------------


db_models.Base.metadata.create_all(engine)


app.add_middleware(
       CORSMiddleware,
       allow_origins=ORIGINS,
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

import asyncio


import time
# from queue import Queue
# task_queue = Queue()

# class Tasks:
#     def __init__(self, task_data):
#         self.task_data = task_data
    
#     def __call__(self):
#         # Do some long-running task with self.task_data
#         for i in range(0, 10):
#             time.sleep(0.3)
#             print(f"{i} task id {self.task_data}")

# @app.post("/background-tasks")
# async def create_task(background_tasks: BackgroundTasks, task_data: str):
#     task = Tasks(task_data)
#     task_queue.put(task)
#     print(task_queue.queue)
#     background_tasks.add_task(task)


queues = []  # initialize empty task queue
current_task = {"id": None, "queue": []}  # initialize current task to None

@app.post("/task",tags=["testing"])
async def process_task(background_task: BackgroundTasks):
    if len(queues) >= 5:
        return {"message": "Task queue is full. Please try again later."}
    
    task_id = len(queues) + 1  # assign unique ID to task
    queues.append(task_id)  # add task to queue
    
    global current_task
    if current_task["id"] is None:  # start the task immediately if there is no current task
        current_task["id"] = task_id
        current_task["task"] = background_task.add_task(process_task_in_background,task_id)
    else:
        # add the task ID to the current task's queue
        current_task["queue"].append(task_id)
    print(queues)
    print(current_task)
    return {"message": f"Your task is being processed in the background. Your task is in queue number {task_id}."}

def process_task_in_background(task_id):
    # await asyncio.sleep(5)
    for i in range(0, 10):
        time.sleep(0.3)
        print(f"{i} task id {task_id}")
    
    global current_task
    if current_task["id"] == task_id:
        current_task["id"] = None  # mark the current task as completed
        queues.remove(task_id)
    
        # start the next task if there is one in the queue
        if len(current_task["queue"]) > 0:
            next_task_id = current_task["queue"].pop(0)
            
            current_task["id"] = next_task_id
            current_task["task"] =  (process_task_in_background(next_task_id))
            

import os
try:
    os.mkdir(f"users/")
except:
    pass

app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(video_reid.router)
app.include_router(live_camera.router)
app.include_router(sync_camera_network.router)
app.include_router(arduino_test.router)


