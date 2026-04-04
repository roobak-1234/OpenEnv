from pydantic import BaseModel
from typing import Literal

class Job(BaseModel):
    id: str
    processing_time: int
    transported: bool = False
    completed: bool = False

class Robot(BaseModel):
    id: str
    type: Literal["mobile", "static"]
    status: Literal["idle", "busy"] = "idle"
