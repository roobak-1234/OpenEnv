from typing import Literal, Optional

from pydantic import BaseModel, Field


class Job(BaseModel):
    id: str
    transport_time: int = Field(ge=1)
    processing_time: int = Field(ge=1)
    transported: bool = False
    completed: bool = False
    in_transport: bool = False
    in_process: bool = False
    transport_remaining_time: int = 0
    processing_remaining_time: int = 0
    assigned_mobile_robot_id: Optional[str] = None
    assigned_static_robot_id: Optional[str] = None


class Robot(BaseModel):
    id: str
    type: Literal["mobile", "static"]
    status: Literal["idle", "busy"] = "idle"
    busy_time_remaining: int = 0
    current_job_id: Optional[str] = None
    current_task: Optional[Literal["transport", "process"]] = None
