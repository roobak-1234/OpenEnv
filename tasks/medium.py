from env.models import Job, Robot
from env.environment import FactoryEnv

def create_env() -> FactoryEnv:
    jobs = [
        Job(
            id=f"job_{i}",
            transport_time=transport_time,
            processing_time=processing_time,
            required_station_type=station_type,
            priority=priority,
            due_step=due_step,
        )
        for i, transport_time, processing_time, station_type, priority, due_step in zip(
            range(1, 6),
            [1, 2, 1, 3, 2],
            [2, 3, 1, 4, 2],
            ["assembly", "welding", "assembly", "welding", "assembly"],
            [3, 5, 2, 4, 4],
            [6, 8, 4, 10, 7],
        )
    ]
    mobile_robots = [Robot(id=f"m_{i}", type="mobile") for i in range(1, 3)]
    static_robots = [
        Robot(id="s_1", type="static", capability="assembly", home_zone="assembly_cell"),
        Robot(id="s_2", type="static", capability="welding", home_zone="welding_cell"),
    ]
    return FactoryEnv(jobs, mobile_robots, static_robots)
