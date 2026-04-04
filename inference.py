import os
import random

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MODEL_NAME = os.getenv("MODEL_NAME", "baseline")
HF_TOKEN = os.getenv("HF_TOKEN", "")
TASK_LEVEL = os.getenv("TASK_LEVEL", "medium")


def choose_action(state):
    jobs = state.get("jobs", [])
    idle_mobile_ids = [robot["id"] for robot in state.get("mobile_robots", []) if robot["status"] == "idle"]
    idle_static_ids = [robot["id"] for robot in state.get("static_robots", []) if robot["status"] == "idle"]

    ready_for_processing = [
        job for job in jobs
        if job["transported"] and not job["completed"] and not job["in_process"]
    ]
    if idle_static_ids and ready_for_processing:
        job = max(ready_for_processing, key=lambda item: (item["processing_time"], -item["transport_time"]))
        return ["process", random.choice(idle_static_ids), job["id"]]

    ready_for_transport = [
        job for job in jobs
        if not job["transported"] and not job["completed"] and not job["in_transport"]
    ]
    if idle_mobile_ids and ready_for_transport:
        job = max(ready_for_transport, key=lambda item: (item["processing_time"], -item["transport_time"]))
        return ["transport", random.choice(idle_mobile_ids), job["id"]]

    return ["wait", None, None]

def run_inference():
    print(f"[START] task=factory_robot env=openenv model={MODEL_NAME}")

    try:
        resp = requests.post(f"{API_BASE_URL}/reset", json={"task": TASK_LEVEL})
        resp.raise_for_status()
        reset_payload = resp.json()
        session_id = reset_payload["session_id"]
        state = reset_payload["state"]

        done = False
        steps = 0
        rewards = []
        max_steps = 100

        while not done and steps < max_steps:
            action = choose_action(state)

            resp = requests.post(
                f"{API_BASE_URL}/step",
                json={"session_id": session_id, "action": action},
            )
            resp.raise_for_status()
            data = resp.json()

            state = data.get("state", {})
            reward = float(data.get("reward", 0.0))
            done = data.get("done", False)
            info = data.get("info", {})
            rewards.append(reward)

            done_str = "true" if done else "false"
            action_str = f"({action[0]}, {action[1]}, {action[2]})" if len(action) == 3 else str(action)
            error = info.get("error", "null")
            print(f"[STEP] step={steps+1} action={action_str} reward={reward:.2f} done={done_str} error={error}")
            steps += 1

        success_str = "true" if done else "false"
        rewards_str = ",".join([f"{r:.2f}" for r in rewards])
        print(f"[END] success={success_str} steps={steps} rewards={rewards_str}")

    except Exception as e:
        print(f"[STEP] step=0 action=none reward=0.00 done=true error={str(e)}")
        print(f"[END] success=false steps=0 rewards=")

if __name__ == "__main__":
    run_inference()
