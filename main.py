from tasks.medium import create_env
from grader.grader import grade


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
    jobs = state["jobs"]
    idle_mobile_ids = [robot["id"] for robot in state["mobile_robots"] if robot["status"] == "idle"]
    idle_static_robots = [robot for robot in state["static_robots"] if robot["status"] == "idle"]

    ready_for_processing = [
        job for job in jobs
        if job["transported"] and not job["completed"] and not job["in_process"]
    ]
    if idle_static_robots and ready_for_processing:
        ranked_jobs = sorted(ready_for_processing, key=lambda item: sort_key(item, state))
        for job in ranked_jobs:
            for robot in idle_static_robots:
                if robot.get("capability") == job["required_station_type"]:
                    return ("process", robot["id"], job["id"])

    ready_for_transport = [
        job for job in jobs
        if not job["transported"] and not job["completed"] and not job["in_transport"]
    ]
    if idle_mobile_ids and ready_for_transport:
        job = sorted(ready_for_transport, key=lambda item: sort_key(item, state))[0]
        return ("transport", idle_mobile_ids[0], job["id"])

    return ("wait", None, None)


def run_baseline():
    env = create_env()
    state = env.reset().model_dump()

    total_reward = 0.0
    done = False
    max_steps = 100
    steps = 0

    print("Starting Factory Robot Simulation Baseline")
    print(f"Initial State: {len(state['jobs'])} jobs, {len(state['mobile_robots'])} mobile robots, {len(state['static_robots'])} static robots")

    while not done and steps < max_steps:
        action = choose_action(state)
        print(f"Step {steps+1} Action: {action}")
        observation, reward, done, info = env.step(action)
        state = observation.model_dump()
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
