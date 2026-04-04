ASSIGNMENT_REWARD = 1.0
TRANSPORT_COMPLETION_REWARD = 4.0
JOB_COMPLETION_REWARD = 10.0
INVALID_ACTION_PENALTY = -3.0
IDLE_ROBOT_PENALTY = 0.15


def calculate_reward(
    action_valid: bool,
    action_type: str | None = None,
    transports_completed: int = 0,
    jobs_completed: int = 0,
    idle_robots: int = 0,
    unfinished_jobs: int = 0,
) -> float:
    if not action_valid:
        return INVALID_ACTION_PENALTY

    reward = 0.0

    if action_type in {"transport", "process"}:
        reward += ASSIGNMENT_REWARD

    reward += transports_completed * TRANSPORT_COMPLETION_REWARD
    reward += jobs_completed * JOB_COMPLETION_REWARD

    if unfinished_jobs > 0:
        reward -= idle_robots * IDLE_ROBOT_PENALTY

    return round(reward, 2)
