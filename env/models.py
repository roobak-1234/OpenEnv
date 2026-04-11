from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class Job(BaseModel):
    id: str
    transport_time: int = Field(ge=1)
    processing_time: int = Field(ge=1)
    required_station_type: Literal["assembly", "welding", "inspection"] = "assembly"
    source_zone: Literal["receiving", "kitting", "qa_hold"] = "receiving"
    priority: int = Field(default=1, ge=1, le=5)
    release_step: int = Field(default=0, ge=0)
    due_step: int = Field(default=1, ge=1)
    transported: bool = False
    completed: bool = False
    late: bool = False
    completed_on_time: bool = False
    in_transport: bool = False
    in_process: bool = False
    transport_remaining_time: int = 0
    processing_remaining_time: int = 0
    accumulated_wait_time: int = 0
    overdue_steps: int = 0
    assigned_mobile_robot_id: Optional[str] = None
    assigned_static_robot_id: Optional[str] = None


class Robot(BaseModel):
    id: str
    type: Literal["mobile", "static"]
    status: Literal["idle", "busy"] = "idle"
    capability: Optional[Literal["assembly", "welding", "inspection"]] = None
    home_zone: str = "dispatch"
    busy_time_remaining: int = 0
    current_job_id: Optional[str] = None
    current_task: Optional[Literal["transport", "process"]] = None


class EpisodeMetrics(BaseModel):
    valid_actions: int = 0
    invalid_actions: int = 0
    wait_actions: int = 0
    jobs_transported: int = 0
    jobs_completed: int = 0
    released_jobs: int = 0
    on_time_completions: int = 0
    late_completions: int = 0
    overdue_job_ticks: int = 0
    priority_weighted_completed: int = 0
    priority_weighted_on_time: int = 0
    busy_robot_ticks: int = 0
    idle_robot_ticks: int = 0
    total_reward: float = 0.0


class FactoryObservation(BaseModel):
    jobs: list[Job]
    mobile_robots: list[Robot]
    static_robots: list[Robot]
    time_step: int = Field(ge=0)
    metrics: EpisodeMetrics


class FactoryAction(BaseModel):
    action_type: Literal["transport", "process", "wait"]
    robot_id: Optional[str] = None
    job_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_action_fields(self) -> "FactoryAction":
        if self.action_type == "wait":
            return self

        if not self.robot_id or not self.job_id:
            raise ValueError("transport/process actions require robot_id and job_id.")

        return self

    def as_tuple(self) -> tuple[Optional[str], Optional[str], Optional[str]]:
        return (self.action_type, self.robot_id, self.job_id)


class FactoryReward(BaseModel):
    value: float
