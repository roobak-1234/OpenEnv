SUCCESSFUL_TRANSPORT = 5
JOB_COMPLETION = 10
INVALID_ACTION = -2

def calculate_reward(action_valid: bool, action_type: str = None) -> int:
    if not action_valid:
        return INVALID_ACTION
    if action_type == "transport":
        return SUCCESSFUL_TRANSPORT
    elif action_type == "process":
        return JOB_COMPLETION
    return 0
