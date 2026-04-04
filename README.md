# Factory Robot OpenEnv Simulation

A complete, OpenEnv-compatible backend-only Python simulation environment for a real-world factory system involving static and mobile robots.

## Real-world Relevance
In modern industrial settings, tasks are often distributed between autonomous mobile robots (AMRs) that transport materials, and static robotic arms or workstations that perform fixed tasks (e.g., assembly, welding). This environment simulates the complex coordination required to optimize these workflows, minimize idle time, and complete jobs efficiently.

## Core Concepts
- **Mobile Robots**: Handle transportation of jobs across the factory floor.
- **Static Robots**: Handle the processing of jobs at fixed workstations.
- **Jobs**: Entities that require transportation first, then processing to be completed.

## Environment Interface

### State Space
The environment state contains:
- `jobs`: List of current jobs and their statuses (id, processing_time, transported, completed)
- `mobile_robots`: List of mobile robots and their statuses
- `static_robots`: List of static robots and their statuses
- `time_step`: Current simulation time step integer

### Action Space
Actions are tuples of the form `(action_type, robot_id, job_id)`.
- `("transport", robot_id, job_id)`: Assigns a mobile robot to transport a job.
- `("process", robot_id, job_id)`: Assigns a static robot to process a transported job.

### Reward Function
- **+5**: Successful transport action
- **+10**: Successful job completion step
- **-2**: Invalid action (e.g., trying to process a job that isn't transported, or using a static robot for transport)

## Task Levels
- `easy`: 2 jobs, 1 mobile robot, 1 static robot.
- `medium`: 5 jobs, 2 mobile robots, 2 static robots. 
- `hard`: 15 jobs, 3 mobile robots, 3 static robots.

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

## Docker Instructions

1. Build the Docker image:
   ```bash
   docker build -t factory-robot-env .
   ```
2. Run the Docker container:
   ```bash
   docker run --rm factory-robot-env
   ```
