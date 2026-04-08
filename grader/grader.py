import math
from typing import Any, Dict


TASK_NAMES = ("easy", "medium", "hard")


def grade(state: Dict[str, Any]) -> float:
    jobs = state.get("jobs", [])
    if not jobs:
        return 0.0

    completed_jobs = sum(1 for job in jobs if job.get("completed", False))
    completion_ratio = float(completed_jobs) / len(jobs)

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
    on_time_ratio = (
        metrics.get("on_time_completions", 0) / max(completed_jobs, 1)
        if completed_jobs
        else 0.0
    )
    late_penalty = metrics.get("late_completions", 0) / len(jobs)

    score = (
        (0.45 * completion_ratio)
        + (0.20 * time_efficiency)
        + (0.15 * action_quality)
        + (0.20 * on_time_ratio)
        - (0.10 * late_penalty)
    )
    score = max(0.0001, min(0.9999, score))
    return round(score, 4)


def grade_task(task_name: str, state: Dict[str, Any]) -> float:
    if task_name not in TASK_NAMES:
        raise ValueError(f"Unsupported task '{task_name}'. Expected one of {TASK_NAMES}.")
    return grade(state)


def list_tasks() -> list[str]:
    return list(TASK_NAMES)
