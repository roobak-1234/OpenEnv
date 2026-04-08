import os
import json
import textwrap
from typing import Any

import requests
from openai import OpenAI

from env.models import FactoryAction
from grader.grader import grade_task, list_tasks

API_KEY = os.environ["API_KEY"]
API_BASE_URL = os.environ["API_BASE_URL"]
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4.1-mini")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
TASK_CONFIG = os.getenv("TASK_LEVEL") or os.getenv("TASKS") or "easy,medium,hard"
BENCHMARK = os.getenv("BENCHMARK_NAME", "factory_robot_openenv")
MAX_STEPS = int(os.getenv("MAX_STEPS", "100"))
SUCCESS_SCORE_THRESHOLD = float(os.getenv("SUCCESS_SCORE_THRESHOLD", "0.6"))

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are scheduling work inside a factory simulation.
    Return exactly one JSON object with keys: action_type, robot_id, job_id.
    Valid action_type values: transport, process, wait.
    Use wait when every useful robot is already busy or no job is ready.
    """
).strip()


def parse_tasks() -> list[str]:
    requested = [part.strip() for part in TASK_CONFIG.split(",") if part.strip()]
    valid_tasks = set(list_tasks())
    return [task for task in requested if task in valid_tasks] or list_tasks()


def observation_summary(state: dict[str, Any]) -> str:
    jobs = state.get("jobs", [])
    mobile = state.get("mobile_robots", [])
    static = state.get("static_robots", [])
    return json.dumps(
        {
            "time_step": state.get("time_step", 0),
            "jobs": jobs,
            "mobile_robots": mobile,
            "static_robots": static,
            "metrics": state.get("metrics", {}),
        },
        separators=(",", ":"),
    )


def estimate_remaining_work(job, state):
    if job["completed"]:
        return 0
    if job["in_process"]:
        return job["processing_remaining_time"]
    if job["transported"]:
        return job["processing_time"]
    if job["in_transport"]:
        return job["transport_remaining_time"] + job["processing_time"]
    return job["transport_time"] + job["processing_time"]


def sort_key(job, state):
    remaining_work = estimate_remaining_work(job, state)
    slack = job["due_step"] - state["time_step"] - remaining_work
    return (slack, -job["priority"], -job["processing_time"], job["id"])


def choose_action(state):
    jobs = state.get("jobs", [])
    idle_mobile_ids = [robot["id"] for robot in state.get("mobile_robots", []) if robot["status"] == "idle"]
    idle_static_robots = [robot for robot in state.get("static_robots", []) if robot["status"] == "idle"]

    ready_for_processing = [
        job for job in jobs
        if job["transported"] and not job["completed"] and not job["in_process"]
    ]
    if idle_static_robots and ready_for_processing:
        ranked_jobs = sorted(ready_for_processing, key=lambda item: sort_key(item, state))
        for job in ranked_jobs:
            for robot in idle_static_robots:
                if robot.get("capability") == job["required_station_type"]:
                    return {"action_type": "process", "robot_id": robot["id"], "job_id": job["id"]}

    ready_for_transport = [
        job for job in jobs
        if not job["transported"] and not job["completed"] and not job["in_transport"]
    ]
    if idle_mobile_ids and ready_for_transport:
        job = sorted(ready_for_transport, key=lambda item: sort_key(item, state))[0]
        return {"action_type": "transport", "robot_id": idle_mobile_ids[0], "job_id": job["id"]}

    return {"action_type": "wait", "robot_id": None, "job_id": None}


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: str | None) -> None:
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error or 'null'}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{reward:.2f}" for reward in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def action_to_string(action: dict[str, Any]) -> str:
    return f"({action.get('action_type')}, {action.get('robot_id')}, {action.get('job_id')})"


def extract_json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if "```" in candidate:
        parts = [part.strip() for part in candidate.split("```") if part.strip()]
        candidate = parts[-1]
        if candidate.lower().startswith("json"):
            candidate = candidate[4:].strip()

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or start >= end:
        raise ValueError("No JSON object found in model output.")

    return json.loads(candidate[start : end + 1])


def get_model_action(client: OpenAI, task_name: str, step: int, state: dict[str, Any], history: list[str]) -> dict[str, Any]:
    prompt = textwrap.dedent(
        f"""
        Task: {task_name}
        Step: {step}
        Recent history: {history[-3:] if history else []}
        Current observation JSON:
        {observation_summary(state)}
        Respond with one JSON object only.
        """
    ).strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=120,
        )
        text = (completion.choices[0].message.content or "").strip()
        payload = extract_json_object(text)
        action = FactoryAction(**payload)
        return action.model_dump()
    except Exception as exc:
        raise RuntimeError(f"Model call failed via API_BASE_URL proxy: {exc}") from exc

def run_task(client: OpenAI, task_name: str) -> None:
    rewards: list[float] = []
    history: list[str] = []
    steps_taken = 0
    score = 0.0
    success = False
    final_state: dict[str, Any] = {}

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        reset_response = requests.post(f"{ENV_BASE_URL}/reset", json={"task": task_name}, timeout=30)
        reset_response.raise_for_status()
        reset_payload = reset_response.json()
        session_id = reset_payload["session_id"]
        state = reset_payload["state"]

        done = False
        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            action = get_model_action(client, task_name, step, state, history)

            step_response = requests.post(
                f"{ENV_BASE_URL}/step",
                json={"session_id": session_id, "action": action},
                timeout=30,
            )
            step_response.raise_for_status()
            payload = step_response.json()

            state = payload.get("state", {})
            final_state = state
            reward = float(payload.get("reward", 0.0))
            done = bool(payload.get("done", False))
            info = payload.get("info", {})
            error = info.get("error")

            rewards.append(reward)
            steps_taken = step
            log_step(step=step, action=action_to_string(action), reward=reward, done=done, error=error)
            history.append(f"step={step} action={action_to_string(action)} reward={reward:.2f}")

            if done:
                break

        if final_state:
            score = max(0.0, min(1.0, float(grade_task(task_name, final_state))))
        success = score >= SUCCESS_SCORE_THRESHOLD
    except Exception:
        success = False
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


def run_inference():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY, max_retries=0, timeout=5.0)
    for task_name in parse_tasks():
        run_task(client, task_name)

if __name__ == "__main__":
    run_inference()
