import math
from typing import Any, Dict


TASK_NAMES = ("easy", "medium", "hard")
MIN_SCORE = 0.001
MAX_SCORE = 0.999


def grade(state: Dict[str, Any]) -> float:
    jobs = state.get("jobs", [])
    if not jobs:
        return MIN_SCORE

    completed_jobs = sum(1 for job in jobs if job.get("completed", False))
    completion_ratio = float(completed_jobs) / len(jobs)
    total_priority = sum(int(job.get("priority", 1)) for job in jobs) or 1
    completed_priority = sum(int(job.get("priority", 1)) for job in jobs if job.get("completed", False))
    weighted_completion_ratio = completed_priority / total_priority

    mobile_robots = max(len(state.get("mobile_robots", [])), 1)
    static_robots = max(len(state.get("static_robots", [])), 1)
    total_transport_time = sum(job.get("transport_time", 1) for job in jobs)
    total_processing_time = sum(job.get("processing_time", 1) for job in jobs)
    critical_path = max(job.get("transport_time", 1) + job.get("processing_time", 1) for job in jobs)
    theoretical_lower_bound = max(
        math.ceil(total_transport_time / mobile_robots),
        math.ceil(total_processing_time / static_robots),
        critical_path,
    )

    elapsed_steps = max(int(state.get("time_step", 0)), 1)
    time_efficiency = min(theoretical_lower_bound / elapsed_steps, 1.0)

    metrics = state.get("metrics", {})
    valid_actions = metrics.get("valid_actions", 0)
    invalid_actions = metrics.get("invalid_actions", 0)
    total_actions = valid_actions + invalid_actions
    action_quality = (valid_actions / total_actions) if total_actions else 1.0
    priority_weighted_completed = metrics.get("priority_weighted_completed", completed_priority)
    priority_weighted_on_time = metrics.get("priority_weighted_on_time", 0)
    on_time_ratio = (
        priority_weighted_on_time / max(priority_weighted_completed, 1)
        if completed_jobs
        else 0.0
    )
    late_penalty = metrics.get("late_completions", 0) / len(jobs)
    overdue_job_ticks = metrics.get("overdue_job_ticks", 0)
    backlog_discipline = max(0.0, 1.0 - (overdue_job_ticks / max(len(jobs) * elapsed_steps, 1)))

    score = (
        (0.30 * completion_ratio)
        + (0.20 * weighted_completion_ratio)
        + (0.20 * time_efficiency)
        + (0.15 * action_quality)
        + (0.10 * on_time_ratio)
        + (0.05 * backlog_discipline)
        - (0.10 * late_penalty)
    )
    score = max(MIN_SCORE, min(MAX_SCORE, score))
    return round(score, 4)


def grade_task(task_name: str, state: Dict[str, Any]) -> float:
    if task_name not in TASK_NAMES:
        raise ValueError(f"Unsupported task '{task_name}'. Expected one of {TASK_NAMES}.")
    return grade(state)


def list_tasks() -> list[str]:
    return list(TASK_NAMES)
