import random

from tasks.medium import create_env
from grader.grader import grade


def choose_action(state):
    jobs = state["jobs"]
    idle_mobile_ids = [robot["id"] for robot in state["mobile_robots"] if robot["status"] == "idle"]
    idle_static_ids = [robot["id"] for robot in state["static_robots"] if robot["status"] == "idle"]

    ready_for_processing = [
        job for job in jobs
        if job["transported"] and not job["completed"] and not job["in_process"]
    ]
    if idle_static_ids and ready_for_processing:
        job = max(ready_for_processing, key=lambda item: (item["processing_time"], -item["transport_time"]))
        return ("process", idle_static_ids[0], job["id"])

    ready_for_transport = [
        job for job in jobs
        if not job["transported"] and not job["completed"] and not job["in_transport"]
    ]
    if idle_mobile_ids and ready_for_transport:
        job = max(ready_for_transport, key=lambda item: (item["processing_time"], -item["transport_time"]))
        return ("transport", random.choice(idle_mobile_ids), job["id"])

    return ("wait", None, None)


def run_baseline():
    env = create_env()
    state = env.reset()

    total_reward = 0.0
    done = False
    max_steps = 100
    steps = 0

    print("Starting Factory Robot Simulation Baseline")
    print(f"Initial State: {len(state['jobs'])} jobs, {len(state['mobile_robots'])} mobile robots, {len(state['static_robots'])} static robots")

    while not done and steps < max_steps:
        action = choose_action(state)
        print(f"Step {steps+1} Action: {action}")
        state, reward, done, info = env.step(action)
        total_reward += reward
        steps += 1
        print(f"Reward: {reward:.2f}, Done: {done}, Info: {info}")

    final_score = grade(state)
    print("\n--- Simulation Complete ---")
    print(f"Total Steps: {steps}")
    print(f"Total Reward: {total_reward:.2f}")
    print(f"Completion Score: {final_score:.2f}")
    print(f"Episode Metrics: {state['metrics']}")

if __name__ == "__main__":
    run_baseline()
