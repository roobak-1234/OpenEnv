from typing import Any, Dict, List, Optional, Tuple

from .models import EpisodeMetrics, FactoryAction, FactoryObservation, Job, Robot
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

    def reset(self) -> FactoryObservation:
        self.jobs = [job.model_copy() for job in self.initial_jobs]
        self.mobile_robots = {robot.id: robot.model_copy() for robot in self.initial_mobile_robots}
        self.static_robots = {robot.id: robot.model_copy() for robot in self.initial_static_robots}
        self.time_step = 0
        self.metrics = self._fresh_metrics()
        return self.state()

    def state(self) -> FactoryObservation:
        return FactoryObservation(
            jobs=[job.model_copy() for job in self.jobs],
            mobile_robots=[self.mobile_robots[robot_id].model_copy() for robot_id in sorted(self.mobile_robots)],
            static_robots=[self.static_robots[robot_id].model_copy() for robot_id in sorted(self.static_robots)],
            time_step=self.time_step,
            metrics=EpisodeMetrics(**self.metrics),
        )

    def step(
        self,
        action: FactoryAction | Tuple[Optional[str], Optional[str], Optional[str]] | List[Optional[str]],
    ) -> Tuple[FactoryObservation, float, bool, Dict[str, Any]]:
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

        waiting_jobs = self._count_waiting_jobs()
        self._increment_wait_times()
        progress = self._advance_time()
        overdue_jobs = self._update_overdue_jobs()
        self.metrics["released_jobs"] = self._count_released_jobs()
        unfinished_jobs = sum(1 for job in self.jobs if not job.completed)

        reward = calculate_reward(
            action_valid=valid,
            action_type=action_type if valid else None,
            transports_completed=progress["transports_completed"],
            jobs_completed=progress["jobs_completed"],
            completed_priority_weight=progress["completed_priority_weight"],
            on_time_completions=progress["on_time_completions"],
            late_completions=progress["late_completions"],
            idle_robots=idle_robots,
            unfinished_jobs=unfinished_jobs,
            waiting_jobs=waiting_jobs,
            overdue_jobs=overdue_jobs,
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
        self.metrics["on_time_completions"] += progress["on_time_completions"]
        self.metrics["late_completions"] += progress["late_completions"]
        self.metrics["overdue_job_ticks"] += overdue_jobs
        self.metrics["priority_weighted_completed"] += progress["completed_priority_weight"]
        self.metrics["priority_weighted_on_time"] += progress["on_time_priority_weight"]
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
            "released_jobs": 0,
            "on_time_completions": 0,
            "late_completions": 0,
            "overdue_job_ticks": 0,
            "priority_weighted_completed": 0,
            "priority_weighted_on_time": 0,
            "busy_robot_ticks": 0,
            "idle_robot_ticks": 0,
            "total_reward": 0.0,
        }

    def _normalize_action(
        self,
        action: FactoryAction | Tuple[Optional[str], Optional[str], Optional[str]] | List[Optional[str]] | Any,
    ) -> Tuple[Tuple[Optional[str], Optional[str], Optional[str]], Optional[str]]:
        if isinstance(action, FactoryAction):
            return action.as_tuple(), None

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
            if not self._job_is_released(target_job):
                return False, (
                    f"Job {target_job.id} has not been released yet. "
                    f"It becomes available at step {target_job.release_step}."
                )
            if target_job.completed or target_job.transported or target_job.in_transport or target_job.in_process:
                return False, f"Job {target_job.id} is not ready for transport."

            self._assign_robot(robot=robot, job=target_job, task="transport", duration=target_job.transport_time)
            info["events"].append(
                f"transport_started:{target_job.id}:{robot.id}:{target_job.source_zone}->{target_job.required_station_type}"
            )
            return True, None

        if action_type == "process":
            robot = self.static_robots.get(robot_id or "")
            if robot is None:
                return False, "Static robot not found."
            if robot.status != "idle":
                return False, f"Static robot {robot.id} is currently busy."
            if not target_job.transported or target_job.completed or target_job.in_process:
                return False, f"Job {target_job.id} is not ready for processing."
            if robot.capability != target_job.required_station_type:
                return False, (
                    f"Static robot {robot.id} cannot process station type "
                    f"{target_job.required_station_type}."
                )

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
        completed_priority_weight = 0
        on_time_priority_weight = 0
        on_time_completions = 0
        late_completions = 0

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
                completed_priority_weight += target_job.priority
                completion_step = self.time_step + 1
                target_job.completed_on_time = completion_step <= target_job.due_step
                target_job.late = not target_job.completed_on_time
                if target_job.completed_on_time:
                    on_time_completions += 1
                    on_time_priority_weight += target_job.priority
                else:
                    late_completions += 1
                events.append(f"processing_completed:{target_job.id}:{robot.id}")

            self._release_robot(robot)

        return {
            "events": events,
            "transports_completed": transports_completed,
            "jobs_completed": jobs_completed,
            "completed_priority_weight": completed_priority_weight,
            "on_time_completions": on_time_completions,
            "on_time_priority_weight": on_time_priority_weight,
            "late_completions": late_completions,
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

    def _count_waiting_jobs(self) -> int:
        return sum(
            1
            for job in self.jobs
            if self._job_is_released(job) and not job.completed and not job.in_transport and not job.in_process
        )

    def _increment_wait_times(self) -> None:
        for job in self.jobs:
            if not self._job_is_released(job) or job.completed or job.in_transport or job.in_process:
                continue
            job.accumulated_wait_time += 1

    def _update_overdue_jobs(self) -> int:
        overdue_jobs = 0
        next_step = self.time_step + 1
        for job in self.jobs:
            if not self._job_is_released(job) or job.completed:
                continue
            if next_step > job.due_step:
                job.overdue_steps += 1
                overdue_jobs += 1
        return overdue_jobs

    def _count_released_jobs(self) -> int:
        return sum(1 for job in self.jobs if self._job_is_released(job))

    def _job_is_released(self, job: Job) -> bool:
        return self.time_step >= job.release_step

    def _find_job(self, job_id: Optional[str]) -> Optional[Job]:
        if job_id is None:
            return None

        for job in self.jobs:
            if job.id == job_id:
                return job

        return None
