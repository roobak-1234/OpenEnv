---
title: OpenEnv Factory Robots
emoji: "🤖"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Factory robot coordination benchmark.
tags:
- openenv
- robotics
- scheduling
- simulation
---

# Factory Robot OpenEnv Simulation

A backend-only manufacturing operations benchmark where an agent acts like a dispatch coordinator for a small factory. The agent decides when to move released work orders from intake buffers to the correct production cell, when to start processing on scarce specialist stations, and when to wait for better timing instead of creating queueing mistakes.

The repository is organized as a benchmark package:
- `env/`: typed environment models, state transitions, and reward shaping
- `tasks/`: easy, medium, and hard task factories
- `grader/`: deterministic normalized scoring helpers
- `server/`: FastAPI wrapper exposing `reset`, `step`, and `state`
- `inference.py`: baseline multi-task inference runner with OpenAI client support

## What Changed

This environment now models a dispatch board instead of a toy two-step workflow:
- Mobile robots become busy for a job's `transport_time`
- Static robots become busy for a job's `processing_time`
- Jobs are released over time from realistic source zones such as `receiving`, `kitting`, and `qa_hold`
- Jobs move through `in_transport`, `transported`, `in_process`, and `completed` states
- Jobs carry due steps, priorities, wait time, overdue time, and required workstation types
- Static robots can only process jobs that match their capability, which creates routing constraints and bottlenecks
- The environment supports a `wait` action so agents can advance time when work is already in flight
- The server creates isolated sessions per episode so multiple agents can interact safely in parallel

## Core Concepts

- **Mobile Robots** move released work orders from source buffers into the right production cell
- **Static Robots** process transported jobs at fixed workstations and each robot has a capability such as assembly, welding, or inspection
- **Jobs** have source zones, release times, due steps, priorities, and required station types, which creates realistic dispatch and SLA tradeoffs
- **Dispatch quality matters** because pushing the wrong job at the wrong time can starve urgent work, build overdue backlog, and miss due steps on high-priority orders

## Why This Benchmark Is Useful

This benchmark is meant to test the kind of operational reasoning humans do in real plants and fulfillment environments:
- selecting which released work order should move next
- respecting specialist resource constraints
- balancing rush jobs against background throughput
- keeping queue growth under control instead of optimizing only final completion

That makes it a better fit for agent evaluation than a toy routing puzzle, because the agent must reason about timing, backlog, priorities, and downstream bottlenecks.

## What Good Agents Need To Do

A strong agent in this environment should:
- recognize when a high-priority released job needs to preempt lower-value background work
- avoid dispatching only the easiest jobs while urgent work becomes overdue
- respect station capability constraints instead of treating every workstation as interchangeable
- use `wait` intentionally when all productive resources are already committed
- keep both throughput and service quality healthy over the full episode, not just at the end

## Environment Interface

### State Space

The environment state contains:
- `jobs`: transport and processing durations, source zone, release step, due step, priority, overdue time, required station type, remaining time, assignment fields, and completion flags
- `mobile_robots`: robot status, busy time remaining, and current assignment
- `static_robots`: robot status, busy time remaining, current assignment, and capability
- `time_step`: current simulation tick
- `metrics`: episode statistics such as valid actions, invalid actions, released jobs, overdue backlog ticks, priority-weighted completions, robot utilization, jobs transported, jobs completed, and total reward

### Action Space

Actions are tuples of the form `(action_type, robot_id, job_id)`.
- `("transport", robot_id, job_id)`: assign an idle mobile robot to an untransported job
- `("process", robot_id, job_id)`: assign an idle static robot to a transported job
- `("wait", None, None)`: advance the simulation without issuing a new assignment

### Reward Function

Rewards now mix action validity, SLA quality, and backlog control:
- valid assignments earn a small shaping reward
- completed transports and completed jobs earn progress rewards
- high-priority completions earn more value than low-priority completions
- on-time completions earn an extra bonus and late completions are penalized
- invalid actions receive the lowest possible reward
- idle robots and unreleased queue growth create penalties while unfinished work remains
- overdue unfinished jobs create an additional penalty to reflect missed service commitments
- per-step rewards are normalized into the `0.0` to `1.0` range for cleaner evaluator integration

### Scoring

The grader combines:
- completion ratio
- priority-weighted completion ratio
- time efficiency versus a theoretical lower bound
- action quality based on valid versus invalid actions
- on-time completion ratio for completed work
- backlog discipline through overdue queue pressure

This makes the score much more useful than completion alone, because an agent can no longer get a strong score by finishing everything late or by always serving low-impact work first.

## Baseline Scores

Reference baseline from `inference.py` against the deployed Hugging Face Space using the OpenAI client with `MODEL_NAME=openai/gpt-4.1-mini`:
- `easy`: `0.929`
- `medium`: `0.909`
- `hard`: `0.863`

These runs completed successfully with normalized per-task scores in the required `0.0` to `1.0` range.

## Baseline Policy

The baseline is intentionally simple but not random. It:
- ranks work by slack to due step, priority, and remaining work
- sends transported jobs to matching specialist stations as soon as capacity is available
- ignores unreleased work orders until they actually enter the backlog
- uses `wait` when productive assignment is not yet possible

This keeps the baseline reproducible while still reflecting sensible dispatch behavior.

## Task Levels

- `easy`: a single-cell assembly desk with one rush order released immediately and one lower-priority follow-up work order released later
- `medium`: a mixed assembly and welding schedule with staged releases, different source buffers, and one specialist welding bottleneck
- `hard`: a multi-cell backlog with assembly, welding, and inspection work, staggered arrivals, rush orders, and enough volume that overdue queue pressure matters

## Expected Failure Modes

Agents tend to underperform when they:
- overuse `wait` while released work is available
- greedily dispatch the first visible job instead of the most time-sensitive job
- ignore specialist bottlenecks and create queues in front of constrained stations
- optimize completion count while letting high-priority work become late
- attempt actions on unreleased jobs or incompatible stations

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
uvicorn server.app:app --reload --port 7860
```

5. Run the HTTP inference client against the server:

```bash
python inference.py
```

The inference script:
- uses the OpenAI client for model calls
- reads `API_BASE_URL`, `API_KEY`, and `MODEL_NAME`
- reads `ENV_BASE_URL` for the environment server
- emits `[START]`, `[STEP]`, and `[END]` logs with normalized scores for each task

## Docker Instructions

1. Build the Docker image:

```bash
docker build -t factory-robot-env .
```

2. Run the container:

```bash
docker run --rm -p 7860:7860 factory-robot-env
```
