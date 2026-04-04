import math
from typing import Any, Dict

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

    score = (0.6 * completion_ratio) + (0.25 * time_efficiency) + (0.15 * action_quality)
    return round(score, 4)
