import os
import requests
import json
import random

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MODEL_NAME = os.getenv("MODEL_NAME", "baseline")
HF_TOKEN = os.getenv("HF_TOKEN", "")

def run_inference():
    print(f"[START] task=factory_robot env=openenv model={MODEL_NAME}")
    
    try:
        resp = requests.post(f"{API_BASE_URL}/reset")
        resp.raise_for_status()
        state = resp.json()
        
        done = False
        steps = 0
        rewards = []
        max_steps = 100
        
        while not done and steps < max_steps:
            # Baseline policy: Alternate between transport and process
            mobile_ids = [r['id'] for r in state.get('mobile_robots', [])]
            static_ids = [r['id'] for r in state.get('static_robots', [])]
            jobs = state.get('jobs', [])
            
            action = None
            if steps % 2 == 0:
                # try transport
                for job in jobs:
                    if not job['transported'] and not job['completed']:
                        action = ["transport", random.choice(mobile_ids), job['id']]
                        break
            else:
                # try process
                for job in jobs:
                    if job['transported'] and not job['completed']:
                        action = ["process", random.choice(static_ids), job['id']]
                        break
            
            if action is None and jobs and mobile_ids:
                # fallback
                action = ["transport", random.choice(mobile_ids), jobs[0]['id']]
            elif action is None:
                 action = ["transport", "m_1", "j_1"]
                 
            resp = requests.post(f"{API_BASE_URL}/step", json={"action": action})
            resp.raise_for_status()
            data = resp.json()
            
            state = data.get('state', {})
            reward = float(data.get('reward', 0.0))
            done = data.get('done', False)
            rewards.append(reward)
            
            done_str = "true" if done else "false"
            action_str = f"({action[0]}, {action[1]}, {action[2]})" if len(action) == 3 else str(action)
            print(f"[STEP] step={steps+1} action={action_str} reward={reward:.2f} done={done_str} error=null")
            steps += 1
            
        success_str = "true" if done else "false"
        rewards_str = ",".join([f"{r:.2f}" for r in rewards])
        print(f"[END] success={success_str} steps={steps} rewards={rewards_str}")
        
    except Exception as e:
        print(f"[STEP] step=0 action=none reward=0.00 done=true error={str(e)}")
        print(f"[END] success=false steps=0 rewards=")
        
if __name__ == "__main__":
    run_inference()
