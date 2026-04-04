from typing import Any, Dict, List, Optional, Tuple

from .models import Job, Robot
from .reward import calculate_reward


class FactoryEnv:
    def __init__(self, jobs: List[Job], mobile_robots: List[Robot], static_robots: List[Robot]):
        self.initial_jobs = [job.model_copy() for job in jobs]
        self.initial_mobile_robots = [robot.model_copy() for robot in mobile_robots]
        self.initial_static_robots = [robot.model_copy() for robot in static_robots]
        self.jobs: List[Job] = []
        self.mobile_robots: Dict[str, Robot] = {}
        self.static_robots: Dict[str, Robot] = {}
        self.time_step = 0
        self.metrics: Dict[str, Any] = {}
        self.reset()

    def reset(self) -> Dict[str, Any]:
        self.jobs = [job.model_copy() for job in self.initial_jobs]
        self.mobile_robots = {robot.id: robot.model_copy() for robot in self.initial_mobile_robots}
        self.static_robots = {robot.id: robot.model_copy() for robot in self.initial_static_robots}
        self.time_step = 0
        self.metrics = self._fresh_metrics()
        return self.state()

    def state(self) -> Dict[str, Any]:
        return {
            "jobs": [job.model_dump() for job in self.jobs],
            "mobile_robots": [self.mobile_robots[robot_id].model_dump() for robot_id in sorted(self.mobile_robots)],
            "static_robots": [self.static_robots[robot_id].model_dump() for robot_id in sorted(self.static_robots)],
            "time_step": self.time_step,
            "metrics": dict(self.metrics),
        }

    def step(
        self,
        action: Tuple[Optional[str], Optional[str], Optional[str]] | List[Optional[str]],
    ) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        normalized_action, validation_error = self._normalize_action(action)
        action_type, robot_id, job_id = normalized_action

        valid = validation_error is None
        info: Dict[str, Any] = {
            "valid_action": False,
            "action_attempted": list(action) if isinstance(action, (list, tuple)) else action,
            "events": [],
        }

        if validation_error is None:
            valid, validation_error = self._apply_action(action_type, robot_id, job_id, info)

        busy_robots, idle_robots = self._capture_utilization()
        self.metrics["busy_robot_ticks"] += busy_robots
        self.metrics["idle_robot_ticks"] += idle_robots

        progress = self._advance_time()
        unfinished_jobs = sum(1 for job in self.jobs if not job.completed)

        reward = calculate_reward(
            action_valid=valid,
            action_type=action_type if valid else None,
            transports_completed=progress["transports_completed"],
            jobs_completed=progress["jobs_completed"],
            idle_robots=idle_robots,
            unfinished_jobs=unfinished_jobs,
        )

        self.time_step += 1
        info["events"].extend(progress["events"])
        info["valid_action"] = valid

        if validation_error is not None:
            info["error"] = validation_error
            self.metrics["invalid_actions"] += 1
        else:
            self.metrics["valid_actions"] += 1
            if action_type == "wait":
                self.metrics["wait_actions"] += 1

        self.metrics["jobs_transported"] += progress["transports_completed"]
        self.metrics["jobs_completed"] += progress["jobs_completed"]
        self.metrics["total_reward"] = round(self.metrics["total_reward"] + reward, 2)

        return self.state(), reward, self._is_done(), info

    def _is_done(self) -> bool:
        return all(job.completed for job in self.jobs)

    def _fresh_metrics(self) -> Dict[str, Any]:
        return {
            "valid_actions": 0,
            "invalid_actions": 0,
            "wait_actions": 0,
            "jobs_transported": 0,
            "jobs_completed": 0,
            "busy_robot_ticks": 0,
            "idle_robot_ticks": 0,
            "total_reward": 0.0,
        }

    def _normalize_action(
        self,
        action: Tuple[Optional[str], Optional[str], Optional[str]] | List[Optional[str]] | Any,
    ) -> Tuple[Tuple[Optional[str], Optional[str], Optional[str]], Optional[str]]:
        if not isinstance(action, (list, tuple)):
            return (None, None, None), "Action must be a list or tuple of length 3."

        if len(action) != 3:
            return (None, None, None), "Action must contain exactly three items: (action_type, robot_id, job_id)."

        action_type, robot_id, job_id = action

        if action_type not in {"transport", "process", "wait"}:
            return (None, None, None), "Unsupported action type. Expected one of: transport, process, wait."

        normalized_robot_id = robot_id if robot_id not in {"", None} else None
        normalized_job_id = job_id if job_id not in {"", None} else None
        return (action_type, normalized_robot_id, normalized_job_id), None

    def _apply_action(
        self,
        action_type: Optional[str],
        robot_id: Optional[str],
        job_id: Optional[str],
        info: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        if action_type == "wait":
            info["events"].append("wait")
            return True, None

        target_job = self._find_job(job_id)
        if target_job is None:
            return False, "Job not found."

        if action_type == "transport":
            robot = self.mobile_robots.get(robot_id or "")
            if robot is None:
                return False, "Mobile robot not found."
            if robot.status != "idle":
                return False, f"Mobile robot {robot.id} is currently busy."
            if target_job.completed or target_job.transported or target_job.in_transport or target_job.in_process:
                return False, f"Job {target_job.id} is not ready for transport."

            self._assign_robot(robot=robot, job=target_job, task="transport", duration=target_job.transport_time)
            info["events"].append(f"transport_started:{target_job.id}:{robot.id}")
            return True, None

        if action_type == "process":
            robot = self.static_robots.get(robot_id or "")
            if robot is None:
                return False, "Static robot not found."
            if robot.status != "idle":
                return False, f"Static robot {robot.id} is currently busy."
            if not target_job.transported or target_job.completed or target_job.in_process:
                return False, f"Job {target_job.id} is not ready for processing."

            self._assign_robot(robot=robot, job=target_job, task="process", duration=target_job.processing_time)
            info["events"].append(f"processing_started:{target_job.id}:{robot.id}")
            return True, None

        return False, "Unsupported action type."

    def _assign_robot(self, robot: Robot, job: Job, task: str, duration: int) -> None:
        robot.status = "busy"
        robot.busy_time_remaining = duration
        robot.current_job_id = job.id
        robot.current_task = task

        if task == "transport":
            job.in_transport = True
            job.transport_remaining_time = duration
            job.assigned_mobile_robot_id = robot.id
        else:
            job.in_process = True
            job.processing_remaining_time = duration
            job.assigned_static_robot_id = robot.id

    def _advance_time(self) -> Dict[str, Any]:
        events: List[str] = []
        transports_completed = 0
        jobs_completed = 0

        for robot in list(self.mobile_robots.values()) + list(self.static_robots.values()):
            if robot.status != "busy":
                continue

            target_job = self._find_job(robot.current_job_id)
            if target_job is None:
                self._release_robot(robot)
                continue

            if robot.current_task == "transport" and target_job.transport_remaining_time > 0:
                target_job.transport_remaining_time -= 1
            elif robot.current_task == "process" and target_job.processing_remaining_time > 0:
                target_job.processing_remaining_time -= 1

            if robot.busy_time_remaining > 0:
                robot.busy_time_remaining -= 1

            if robot.busy_time_remaining != 0:
                continue

            if robot.current_task == "transport":
                target_job.in_transport = False
                target_job.transported = True
                target_job.transport_remaining_time = 0
                target_job.assigned_mobile_robot_id = None
                transports_completed += 1
                events.append(f"transport_completed:{target_job.id}:{robot.id}")
            elif robot.current_task == "process":
                target_job.in_process = False
                target_job.completed = True
                target_job.processing_remaining_time = 0
                target_job.assigned_static_robot_id = None
                jobs_completed += 1
                events.append(f"processing_completed:{target_job.id}:{robot.id}")

            self._release_robot(robot)

        return {
            "events": events,
            "transports_completed": transports_completed,
            "jobs_completed": jobs_completed,
        }

    def _release_robot(self, robot: Robot) -> None:
        robot.status = "idle"
        robot.busy_time_remaining = 0
        robot.current_job_id = None
        robot.current_task = None

    def _capture_utilization(self) -> Tuple[int, int]:
        robots = list(self.mobile_robots.values()) + list(self.static_robots.values())
        busy_robots = sum(1 for robot in robots if robot.status == "busy")
        return busy_robots, len(robots) - busy_robots

    def _find_job(self, job_id: Optional[str]) -> Optional[Job]:
        if job_id is None:
            return None

        for job in self.jobs:
            if job.id == job_id:
                return job

        return None
