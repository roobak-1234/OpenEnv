ASSIGNMENT_REWARD = 0.10
TRANSPORT_COMPLETION_REWARD = 0.20
JOB_COMPLETION_REWARD = 0.50
INVALID_ACTION_REWARD = 0.00
IDLE_ROBOT_PENALTY = 0.03


def calculate_reward(
    action_valid: bool,
    action_type: str | None = None,
    transports_completed: int = 0,
    jobs_completed: int = 0,
    idle_robots: int = 0,
    unfinished_jobs: int = 0,
) -> float:
    if not action_valid:
        return INVALID_ACTION_REWARD

    reward = 0.0

    if action_type in {"transport", "process"}:
        reward += ASSIGNMENT_REWARD

    reward += transports_completed * TRANSPORT_COMPLETION_REWARD
    reward += jobs_completed * JOB_COMPLETION_REWARD

    if unfinished_jobs > 0:
        reward -= idle_robots * IDLE_ROBOT_PENALTY

    reward = max(0.0, min(1.0, reward))
    return round(reward, 2)
