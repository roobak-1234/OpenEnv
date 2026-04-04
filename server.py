from typing import List, Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

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


class StepRequest(BaseModel):
    session_id: str = Field(min_length=1)
    action: List[Optional[str]]

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: List[Optional[str]]) -> List[Optional[str]]:
        if len(value) != 3:
            raise ValueError("Action must contain exactly three items.")
        if value[0] not in {"transport", "process", "wait"}:
            raise ValueError("Action type must be one of: transport, process, wait.")
        return value

@app.post("/reset")
def reset_env(payload: ResetRequest | None = None):
    task = payload.task if payload is not None else "medium"
    env = TASK_BUILDERS[task]()
    session_id = str(uuid4())
    SESSIONS[session_id] = env
    state = env.reset()
    return {
        "session_id": session_id,
        "task": task,
        "state": state,
    }

@app.post("/step")
def step_env(payload: StepRequest):
    env = SESSIONS.get(payload.session_id)
    if env is None:
        raise HTTPException(status_code=404, detail="Session not found. Call /reset to create a new episode.")

    action = tuple(payload.action)
    state, reward, done, info = env.step(action)

    return {
        "state": state,
        "reward": float(reward),
        "done": bool(done),
        "info": info,
    }
