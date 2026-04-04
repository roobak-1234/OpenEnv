from typing import Tuple, Dict, Any, List
from .models import Job, Robot
from .reward import calculate_reward

class FactoryEnv:
    def __init__(self, jobs: List[Job], mobile_robots: List[Robot], static_robots: List[Robot]):
        self.initial_jobs = [job.model_copy() for job in jobs]
        self.initial_mobile_robots = [r.model_copy() for r in mobile_robots]
        self.initial_static_robots = [r.model_copy() for r in static_robots]
        self.jobs: List[Job] = []
        self.mobile_robots: Dict[str, Robot] = {}
        self.static_robots: Dict[str, Robot] = {}
        self.time_step = 0
        self.reset()
        
    def reset(self) -> Dict[str, Any]:
        self.jobs = [job.model_copy() for job in self.initial_jobs]
        self.mobile_robots = {r.id: r.model_copy() for r in self.initial_mobile_robots}
        self.static_robots = {r.id: r.model_copy() for r in self.initial_static_robots}
        self.time_step = 0
        return self.state()
        
    def state(self) -> Dict[str, Any]:
        return {
            "jobs": [job.model_dump() for job in self.jobs],
            "mobile_robots": [r.model_dump() for r in self.mobile_robots.values()],
            "static_robots": [r.model_dump() for r in self.static_robots.values()],
            "time_step": self.time_step
        }
        
    def step(self, action: Tuple[str, str, str]) -> Tuple[Dict[str, Any], int, bool, Dict[str, Any]]:
        # action is of form (action_type, robot_id, job_id)
        # action_type in ["transport", "process"]
        
        action_type, robot_id, job_id = action
        
        reward = 0
        valid = False
        
        # Find job
        target_job = None
        for job in self.jobs:
            if job.id == job_id:
                target_job = job
                break
                
        if target_job is None:
            reward = calculate_reward(False)
            self.time_step += 1
            return self.state(), reward, self._is_done(), {"error": "Job not found", "valid_action": False}
            
        if action_type == "transport":
            if robot_id in self.mobile_robots and not target_job.transported and not target_job.completed:
                target_job.transported = True
                valid = True
                reward = calculate_reward(True, "transport")
            else:
                reward = calculate_reward(False)
                
        elif action_type == "process":
            if robot_id in self.static_robots and target_job.transported and not target_job.completed:
                target_job.completed = True
                valid = True
                reward = calculate_reward(True, "process")
            else:
                reward = calculate_reward(False)
        else:
            reward = calculate_reward(False)
            
        self.time_step += 1
        
        info = {
            "valid_action": valid,
            "action_attempted": action
        }
        
        return self.state(), reward, self._is_done(), info
        
    def _is_done(self) -> bool:
        return all(job.completed for job in self.jobs)
