from typing import Dict, Any

def grade(state: Dict[str, Any]) -> float:
    jobs = state.get("jobs", [])
    if not jobs:
        return 0.0
    
    completed_jobs = sum(1 for job in jobs if job.get("completed", False))
    return float(completed_jobs) / len(jobs)
