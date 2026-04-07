---
title: OpenEnv Factory Robots
emoji: "🤖"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: OpenEnv-compatible factory robot coordination benchmark with FastAPI and Docker.
---

# Factory Robot OpenEnv Simulation

A backend-only Python simulation for training AI agents to coordinate mobile and static robots in a factory workflow.

The repository is organized as a benchmark package:
- `env/`: typed environment models, state transitions, and reward shaping
- `tasks/`: easy, medium, and hard task factories
- `grader/`: deterministic normalized scoring helpers
- `server.py`: FastAPI wrapper exposing `reset`, `step`, and `state`
- `inference.py`: baseline multi-task inference runner with OpenAI client support

## What Changed

This environment now models time instead of flipping jobs directly from "not started" to "done":
- Mobile robots become busy for a job's `transport_time`
- Static robots become busy for a job's `processing_time`
- Jobs move through `in_transport`, `transported`, `in_process`, and `completed` states
- The environment supports a `wait` action so agents can advance time when work is already in flight
- The server creates isolated sessions per episode so multiple agents can interact safely in parallel

## Core Concepts

- **Mobile Robots** move work between stations
- **Static Robots** process transported jobs at fixed workstations
- **Jobs** have both `transport_time` and `processing_time`, which creates real scheduling tradeoffs

## Environment Interface

### State Space

The environment state contains:
- `jobs`: transport and processing durations, remaining time, assignment fields, and completion flags
- `mobile_robots`: robot status, busy time remaining, and current assignment
- `static_robots`: robot status, busy time remaining, and current assignment
- `time_step`: current simulation tick
- `metrics`: episode statistics such as valid actions, invalid actions, robot utilization, jobs transported, jobs completed, and total reward

### Action Space

Actions are tuples of the form `(action_type, robot_id, job_id)`.
- `("transport", robot_id, job_id)`: assign an idle mobile robot to an untransported job
- `("process", robot_id, job_id)`: assign an idle static robot to a transported job
- `("wait", None, None)`: advance the simulation without issuing a new assignment

### Reward Function

Rewards now mix action validity, finished work, and utilization:
- valid assignments earn a small shaping reward
- completed transports and completed jobs earn progress rewards
- invalid actions receive the lowest possible reward
- idle robots create a small penalty while unfinished work remains
- per-step rewards are normalized into the `0.0` to `1.0` range for cleaner evaluator integration

### Scoring

The grader combines:
- completion ratio
- time efficiency versus a theoretical lower bound
- action quality based on valid versus invalid actions

This makes the score much more useful for learning than completion alone.

## Task Levels

- `easy`: 2 jobs, 1 mobile robot, 1 static robot
- `medium`: 5 jobs, 2 mobile robots, 2 static robots
- `hard`: 15 jobs, 3 mobile robots, 3 static robots

## API Contract

### `POST /reset`

Creates a fresh session and returns:
- `session_id`
- `task`
- `state`

Optional JSON body:

```json
{"task": "medium"}
```

### `POST /step`

Requires:

```json
{
  "session_id": "your-session-id",
  "action": {
    "action_type": "transport",
    "robot_id": "m_1",
    "job_id": "job_1"
  }
}
```

Malformed actions are rejected with a client error instead of crashing the server.

### `GET /state`

Returns the current observation for a session:

```text
/state?session_id=<your-session-id>
```

## Setup and Running Locally

1. Create a virtual environment and activate it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the baseline simulation:

```bash
python main.py
```

4. Run the API server:

```bash
uvicorn server:app --reload
```

5. Run the HTTP inference client against the server:

```bash
python inference.py
```

The inference script:
- uses the OpenAI client for model calls
- reads `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` or `OPENAI_API_KEY`
- reads `ENV_BASE_URL` for the environment server
- emits `[START]`, `[STEP]`, and `[END]` logs with normalized scores for each task

## Docker Instructions

1. Build the Docker image:

```bash
docker build -t factory-robot-env .
```

2. Run the container:

```bash
docker run --rm -p 8000:8000 factory-robot-env
```
