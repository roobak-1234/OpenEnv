from env.models import Job, Robot
from env.environment import FactoryEnv

def create_env() -> FactoryEnv:
    jobs = [Job(id=f"job_{i}", processing_time=t) for i, t in zip(range(1, 6), [2, 3, 1, 4, 2])]
    mobile_robots = [Robot(id=f"m_{i}", type="mobile") for i in range(1, 3)]
    static_robots = [Robot(id=f"s_{i}", type="static") for i in range(1, 3)]
    return FactoryEnv(jobs, mobile_robots, static_robots)
