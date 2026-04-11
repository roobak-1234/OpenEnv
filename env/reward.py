ASSIGNMENT_REWARD = 0.10
TRANSPORT_COMPLETION_REWARD = 0.15
JOB_COMPLETION_REWARD = 0.25
PRIORITY_WEIGHT_REWARD = 0.03
ON_TIME_COMPLETION_BONUS = 0.18
LATE_COMPLETION_PENALTY = 0.08
INVALID_ACTION_REWARD = 0.00
IDLE_ROBOT_PENALTY = 0.02
WAITING_JOB_PENALTY = 0.01
OVERDUE_JOB_PENALTY = 0.02


def calculate_reward(
    action_valid: bool,
    action_type: str | None = None,
    transports_completed: int = 0,
    jobs_completed: int = 0,
    completed_priority_weight: int = 0,
    on_time_completions: int = 0,
    late_completions: int = 0,
    idle_robots: int = 0,
    unfinished_jobs: int = 0,
    waiting_jobs: int = 0,
    overdue_jobs: int = 0,
) -> float:
    if not action_valid:
        return INVALID_ACTION_REWARD

    reward = 0.0

    if action_type in {"transport", "process"}:
        reward += ASSIGNMENT_REWARD

    reward += transports_completed * TRANSPORT_COMPLETION_REWARD
    reward += jobs_completed * JOB_COMPLETION_REWARD
    reward += completed_priority_weight * PRIORITY_WEIGHT_REWARD
    reward += on_time_completions * ON_TIME_COMPLETION_BONUS
    reward -= late_completions * LATE_COMPLETION_PENALTY

    if unfinished_jobs > 0:
        reward -= idle_robots * IDLE_ROBOT_PENALTY
        reward -= waiting_jobs * WAITING_JOB_PENALTY
        reward -= overdue_jobs * OVERDUE_JOB_PENALTY

    reward = max(0.0, min(1.0, reward))
    return round(reward, 2)
