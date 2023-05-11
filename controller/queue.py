import asyncio

queue = []  # initialize empty task queue

current_task = {"id": None, "queue": []}  # initialize current task to None

task_completed_event = asyncio.Event()