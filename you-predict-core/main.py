"""FastAPI application entrypoint for You Predict Core.

Three trigger surfaces share this single Cloud Run deployment:
  - GET/POST /webhook  — PubSubHubbub push notifications
  - POST /tasks/*      — Cloud Tasks fan-out handlers
  - POST /pipelines/*  — Cloud Scheduler triggered pipelines
"""

import logging

from fastapi import FastAPI

from src.services.pipelines import router as pipelines_router
from src.services.snapshot_handler import router as tasks_router
from src.services.webhook import router as webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="You Predict Core")

app.include_router(webhook_router)
app.include_router(tasks_router)
app.include_router(pipelines_router)
