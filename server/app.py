import os
from typing import Literal
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from env.models import FactoryAction, FactoryObservation
from tasks.easy import create_env as create_easy_env
from tasks.hard import create_env as create_hard_env
from tasks.medium import create_env as create_medium_env

app = FastAPI()
TASK_BUILDERS = {
    "easy": create_easy_env,
    "medium": create_medium_env,
    "hard": create_hard_env,
}
SESSIONS = {}


class ResetRequest(BaseModel):
    task: Literal["easy", "medium", "hard"] = "medium"


class ResetResponse(BaseModel):
    session_id: str
    task: Literal["easy", "medium", "hard"]
    state: FactoryObservation


class StepRequest(BaseModel):
    session_id: str = Field(min_length=1)
    action: FactoryAction


class StepResponse(BaseModel):
    state: FactoryObservation
    reward: float
    done: bool
    info: dict


class StateResponse(BaseModel):
    session_id: str
    task: Literal["easy", "medium", "hard"]
    state: FactoryObservation

@app.post("/reset")
def reset_env(payload: ResetRequest | None = None) -> ResetResponse:
    task = payload.task if payload is not None else "medium"
    env = TASK_BUILDERS[task]()
    session_id = str(uuid4())
    SESSIONS[session_id] = {"task": task, "env": env}
    state = env.reset()
    return ResetResponse(session_id=session_id, task=task, state=state)

@app.post("/step")
def step_env(payload: StepRequest) -> StepResponse:
    session = SESSIONS.get(payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found. Call /reset to create a new episode.")

    state, reward, done, info = session["env"].step(payload.action)

    return StepResponse(state=state, reward=float(reward), done=bool(done), info=info)


@app.get("/state")
def state_env(session_id: str) -> StateResponse:
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found. Call /reset to create a new episode.")

    return StateResponse(session_id=session_id, task=session["task"], state=session["env"].state())


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
