ASSIGNMENT_REWARD = 0.10
TRANSPORT_COMPLETION_REWARD = 0.15
JOB_COMPLETION_REWARD = 0.35
ON_TIME_COMPLETION_BONUS = 0.20
LATE_COMPLETION_PENALTY = 0.10
INVALID_ACTION_REWARD = 0.00
IDLE_ROBOT_PENALTY = 0.02
WAITING_JOB_PENALTY = 0.01


def calculate_reward(
    action_valid: bool,
    action_type: str | None = None,
    transports_completed: int = 0,
    jobs_completed: int = 0,
    on_time_completions: int = 0,
    late_completions: int = 0,
    idle_robots: int = 0,
    unfinished_jobs: int = 0,
    waiting_jobs: int = 0,
) -> float:
    if not action_valid:
        return INVALID_ACTION_REWARD

    reward = 0.0

    if action_type in {"transport", "process"}:
        reward += ASSIGNMENT_REWARD

    reward += transports_completed * TRANSPORT_COMPLETION_REWARD
    reward += jobs_completed * JOB_COMPLETION_REWARD
    reward += on_time_completions * ON_TIME_COMPLETION_BONUS
    reward -= late_completions * LATE_COMPLETION_PENALTY

    if unfinished_jobs > 0:
        reward -= idle_robots * IDLE_ROBOT_PENALTY
        reward -= waiting_jobs * WAITING_JOB_PENALTY

    reward = max(0.0, min(1.0, reward))
    return round(reward, 2)
