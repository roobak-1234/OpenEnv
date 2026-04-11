from env.models import Job, Robot
from env.environment import FactoryEnv

def create_env() -> FactoryEnv:
    jobs = [
        Job(
            id="job_1",
            transport_time=1,
            processing_time=2,
            required_station_type="assembly",
            source_zone="receiving",
            priority=5,
            release_step=0,
            due_step=4,
        ),
        Job(
            id="job_2",
            transport_time=2,
            processing_time=2,
            required_station_type="assembly",
            source_zone="kitting",
            priority=2,
            release_step=2,
            due_step=8,
        ),
    ]
    mobile_robots = [Robot(id="m_1", type="mobile")]
    static_robots = [Robot(id="s_1", type="static", capability="assembly", home_zone="assembly_cell")]
    return FactoryEnv(jobs, mobile_robots, static_robots)
