import logging
import os
from contextlib import asynccontextmanager
from os import path

import fastapi

import utils
from download import download_missing
from manager import Manager

uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.handlers.clear()
uvicorn_error_logger = logging.getLogger("uvicorn.error")
uvicorn_error_logger.handlers.clear()
uvicorn_error_logger.addHandler(utils.handler("Uvicorn"))
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.handlers.clear()
uvicorn_access_logger.addHandler(utils.handler("Access", utils.AccessFormatter))

fastapi_logger = logging.getLogger("fastapi")
fastapi_logger.handlers.clear()
fastapi_logger.addHandler(utils.handler("FastAPI"))

manager: Manager = None


@asynccontextmanager
async def lifespan(*args):
    global manager
    download_missing()
    manager = Manager()

    yield


app = fastapi.FastAPI(
    lifespan=lifespan,
    title="AIC Swarm Manager"
)


@app.get("/file/{content}/{file_path:path}")
def get_file(content: str, file_path: str):
    match content:
        case "keyframes":
            root = utils.keyframes
        case "objects":
            root = utils.objects
        case _:
            raise fastapi.HTTPException(status_code=404)

    root = path.join(root, file_path)

    if not path.exists(root):
        raise fastapi.HTTPException(status_code=404)

    if path.isdir(root):
        return sorted(os.listdir(root)) or []
    else:
        return fastapi.responses.FileResponse(root)


@app.get("/status")
def get_status():
    return {
        "pending": len(manager.pending),
        "processing": len(manager.processing)
    }


@app.get("/pending")
def get_pending():
    return manager.pending


@app.get("/processing")
def get_processing():
    return manager.processing


@app.websocket("/session")
async def session(websocket: fastapi.WebSocket):
    await websocket.accept()

    item: str = None

    async for raw in websocket.iter_json():
        command, data = raw

        if command == "process":
            item = manager.process()
            await websocket.send_text(item)
        elif command == "interrupt":
            manager.interrupt(item)
            item = None
        elif command == "finish":
            manager.finish(item, data)
            item = None
        else:
            await websocket.send_json({"error": "Invalid command"})

    if item:
        manager.interrupt(item)
