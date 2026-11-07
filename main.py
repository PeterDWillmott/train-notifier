import threading
from collections import deque
from contextlib import asynccontextmanager

from fastapi import FastAPI

from consume_darwin import run_consumer

# Keep only the 50 most recent messages; older ones drop off automatically
recent_messages = deque(maxlen=50)
stop_event = threading.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run the blocking Kafka consumer in a background thread
    thread = threading.Thread(
        target=run_consumer,
        args=(recent_messages.append, stop_event),
        daemon=True,
    )
    thread.start()
    yield
    # Shutdown: tell the consumer loop to stop and wait for it to close
    stop_event.set()
    thread.join(timeout=5)


app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Train Notifier API is running"}

@app.get("/messages")
def get_messages():
    return list(recent_messages)
