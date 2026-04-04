import random
from tasks.medium import create_env
from grader.grader import grade

def run_baseline():
    env = create_env()
    state = env.reset()
    
    total_reward = 0
    done = False
    max_steps = 100
    steps = 0
    
    print("Starting Factory Robot Simulation Baseline")
    print(f"Initial State: {len(state['jobs'])} jobs, {len(state['mobile_robots'])} mobile robots, {len(state['static_robots'])} static robots")
    
    while not done and steps < max_steps:
        # Determine possible actions
        mobile_ids = [r['id'] for r in state['mobile_robots']]
        static_ids = [r['id'] for r in state['static_robots']]
        
        # Simple heuristic or random choice
        # First try to find a job that can be transported
        action = None
        for job in state['jobs']:
            if not job['transported'] and not job['completed']:
                action = ("transport", random.choice(mobile_ids), job['id'])
                break
        
        # Then try to find a job that can be processed
        if action is None:
            for job in state['jobs']:
                if job['transported'] and not job['completed']:
                    action = ("process", random.choice(static_ids), job['id'])
                    break
        
        # If no valid logic, just pick a random completely invalid action
        if action is None:
            action = ("transport", random.choice(mobile_ids), state['jobs'][0]['id'])
            
        print(f"Step {steps+1} Action: {action}")
        state, reward, done, info = env.step(action)
        total_reward += reward
        steps += 1
        print(f"Reward: {reward}, Done: {done}")
        
    final_score = grade(state)
    print("\\n--- Simulation Complete ---")
    print(f"Total Steps: {steps}")
    print(f"Total Reward: {total_reward}")
    print(f"Completion Score: {final_score:.2f}")

if __name__ == "__main__":
    run_baseline()
