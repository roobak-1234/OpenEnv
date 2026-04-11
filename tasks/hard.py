from env.models import Job, Robot
from env.environment import FactoryEnv

def create_env() -> FactoryEnv:
    jobs = [
        Job(
            id=f"job_{i}",
            transport_time=transport_time,
            processing_time=processing_time,
            required_station_type=station_type,
            source_zone=source_zone,
            priority=priority,
            release_step=release_step,
            due_step=due_step,
        )
        for i, transport_time, processing_time, station_type, source_zone, priority, release_step, due_step in zip(
            range(1, 16),
            [1, 2, 1, 3, 2, 4, 2, 1, 3, 4, 2, 3, 1, 2, 4],
            [2, 3, 1, 4, 2, 5, 2, 1, 3, 4, 2, 2, 1, 3, 5],
            [
                "assembly",
                "welding",
                "inspection",
                "welding",
                "assembly",
                "inspection",
                "assembly",
                "inspection",
                "welding",
                "inspection",
                "assembly",
                "welding",
                "inspection",
                "assembly",
                "inspection",
            ],
            [
                "receiving",
                "receiving",
                "qa_hold",
                "kitting",
                "receiving",
                "qa_hold",
                "kitting",
                "receiving",
                "kitting",
                "qa_hold",
                "receiving",
                "kitting",
                "qa_hold",
                "receiving",
                "qa_hold",
            ],
            [3, 5, 2, 4, 3, 5, 2, 1, 4, 5, 3, 4, 2, 3, 5],
            [0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6],
            [7, 9, 5, 11, 8, 13, 8, 7, 10, 14, 9, 11, 8, 10, 15],
        )
    ]
    mobile_robots = [Robot(id=f"m_{i}", type="mobile") for i in range(1, 4)]
    static_robots = [
        Robot(id="s_1", type="static", capability="assembly", home_zone="assembly_cell"),
        Robot(id="s_2", type="static", capability="welding", home_zone="welding_cell"),
        Robot(id="s_3", type="static", capability="inspection", home_zone="inspection_cell"),
    ]
    return FactoryEnv(jobs, mobile_robots, static_robots)
