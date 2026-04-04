from env.models import Job, Robot
from env.environment import FactoryEnv

def create_env() -> FactoryEnv:
    jobs = [
        Job(id="job_1", processing_time=2),
        Job(id="job_2", processing_time=3)
    ]
    mobile_robots = [Robot(id="m_1", type="mobile")]
    static_robots = [Robot(id="s_1", type="static")]
    return FactoryEnv(jobs, mobile_robots, static_robots)
