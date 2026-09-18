"""FastAPI + SSE backend for the Pitchside dashboard.

Run with: uvicorn api.main:app --reload --port 8000
"""
import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.runner import manager
from pipeline import db
from pipeline.poison import SCENARIOS

RESULTS_DIR = Path(__file__).resolve().parents[1] / "evals" / "results"

app = FastAPI(title="Pitchside API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartRequest(BaseModel):
    scenario_ids: list[int] = []
    delay: float = 0.15
    provider: str = "groq"


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/runs/start")
def start_run(req: StartRequest):
    unknown = [sid for sid in req.scenario_ids if sid not in SCENARIOS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"unknown scenario ids: {unknown}")
    try:
        manager.start(req.scenario_ids, req.delay, req.provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"status": "started", "scenario_ids": req.scenario_ids, "provider": req.provider}


@app.post("/runs/stop")
def stop_run():
    manager.stop()
    return {"status": "stopping"}


@app.get("/runs/status")
def run_status():
    return {"running": manager.is_running()}


@app.get("/scenarios")
def list_scenarios():
    return [
        {"id": sid, "name": s["name"], "expected_action": s["expected_action"]}
        for sid, s in sorted(SCENARIOS.items())
    ]


@app.get("/stats")
def stats():
    return db.stats(manager.conn)


@app.get("/audit")
def audit(limit: int = 200):
    return db.recent_audit(manager.conn, limit)


@app.get("/rules")
def rules_list():
    return db.list_rules(manager.conn)


@app.get("/evals")
def evals_list():
    if not RESULTS_DIR.exists():
        return []
    return sorted(p.name for p in RESULTS_DIR.glob("*.json"))


@app.get("/evals/{filename}")
def evals_detail(filename: str):
    path = (RESULTS_DIR / filename).resolve()
    if RESULTS_DIR.resolve() not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return json.loads(path.read_text())


@app.get("/events/stream")
async def stream():
    q = manager.subscribe()

    async def gen():
        try:
            while True:
                msg = await asyncio.to_thread(q.get)
                yield f"data: {json.dumps(msg, default=str)}\n\n"
        finally:
            manager.unsubscribe(q)

    return StreamingResponse(gen(), media_type="text/event-stream")
