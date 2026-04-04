from env.models import Job, Robot
from env.environment import FactoryEnv

def create_env() -> FactoryEnv:
    jobs = [Job(id=f"job_{i}", processing_time=t) for i, t in zip(range(1, 16), [2, 3, 1, 4, 2, 5, 2, 1, 3, 4, 2, 2, 1, 3, 5])]
    mobile_robots = [Robot(id=f"m_{i}", type="mobile") for i in range(1, 4)]
    static_robots = [Robot(id=f"s_{i}", type="static") for i in range(1, 4)]
    return FactoryEnv(jobs, mobile_robots, static_robots)
