from env.models import Job, Robot
from env.environment import FactoryEnv

def create_env() -> FactoryEnv:
    jobs = [
        Job(id=f"job_{i}", transport_time=transport_time, processing_time=processing_time)
        for i, transport_time, processing_time in zip(
            range(1, 6),
            [1, 2, 1, 3, 2],
            [2, 3, 1, 4, 2],
        )
    ]
    mobile_robots = [Robot(id=f"m_{i}", type="mobile") for i in range(1, 3)]
    static_robots = [Robot(id=f"s_{i}", type="static") for i in range(1, 3)]
    return FactoryEnv(jobs, mobile_robots, static_robots)
