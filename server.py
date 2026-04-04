from fastapi import FastAPI, Request
from tasks.medium import create_env

app = FastAPI()
env = create_env()

@app.post("/reset")
def reset_env():
    state = env.reset()
    return state
    
@app.post("/step")
async def step_env(request: Request):
    data = await request.json()
    action = data.get("action")
    
    # If action is a list (from JSON), convert back to tuple for the environment
    if isinstance(action, list):
        action = tuple(action)
        
    state, reward, done, info = env.step(action)
    
    return {
        "state": state,
        "reward": float(reward) if reward else 0.0,
        "done": bool(done)
    }
