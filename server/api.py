from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import subprocess
import os
import sys
import hashlib
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_FILE = "server/logs/agent.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Clear log on startup
with open(LOG_FILE, "w") as f:
    f.write("[System] Agent Initialized. Waiting for Directive...\n")

def run_agent_process(industry: str):
    """
    Runs the agent loop (Generate -> Validate) and pipes output to LOG_FILE.
    """
    with open(LOG_FILE, "a") as log:
        log.write(f"\n[Directive] Generate content for: {industry}\n")
        log.write("[Orchestrator] Activating Schema Forge...\n")
        log.flush()

        # Step 1: Generate
        log.write("[Schema Forge] Drafting schema (Template/LLM)...\n")
        log.flush()
        
        # Determine Python Executable
        python_exec = sys.executable 
        # Ideally use the venv python if running from venv, but sys.executable is safer here 
        # if we assume this script is run with the correct python.
        
        output_dir = f"protocol/lib/{industry.lower().replace(' ', '_')}"
        
        try:
            # Run Generator
            gen_cmd = [python_exec, "execution/generate_schema.py", "--industry", industry, "--output", output_dir]
            result = subprocess.run(gen_cmd, capture_output=True, text=True)
            log.write(result.stdout)
            if result.stderr:
                log.write(f"[Error] {result.stderr}\n")
            
            if result.returncode != 0:
                log.write("[Orchestrator] Generation Failed. Aborting.\n")
                return

            # Step 2: Validate
            log.write("[Orchestrator] Validating generated artifacts...\n")
            log.flush()
            
            val_cmd = [python_exec, "execution/validate_and_feedback.py", "--path", output_dir]
            val_result = subprocess.run(val_cmd, capture_output=True, text=True)
            
            # The validation script prints JSON. We want to log a human friendly version.
            log.write(val_result.stdout) 
            # In a real agent, we'd parse this JSON and "Self-Anneal" if validation failed.
            # For this demo, we just show the output.
            
            log.write("\n[Orchestrator] Task Complete.\n")
            
        except Exception as e:
            log.write(f"[System Critical] {str(e)}\n")

@app.post("/agent/generate")
async def generate_schema(industry: str, background_tasks: BackgroundTasks):
    """
    Trigger the agent loop in the background.
    """
    background_tasks.add_task(run_agent_process, industry)
    return {"status": "Agent Activated", "target": industry}

import json

@app.get("/api/protocol/library")
async def get_library():
    lib_path = "protocol/lib"
    if not os.path.exists(lib_path):
        return []
    # List directories in protocol/lib
    dirs = [d for d in os.listdir(lib_path) if os.path.isdir(os.path.join(lib_path, d))]
    return sorted(dirs)

from odgs.scripts.hashing import get_deterministic_json_hash

@app.get("/api/protocol/bundle/{industry}")
async def get_bundle(industry: str):
    industry_path = os.path.join("protocol/lib", industry)
    if not os.path.exists(industry_path):
        # Check if it was provided as a slug
        potential_dir = industry.lower().replace(" ", "_")
        industry_path = os.path.join("protocol/lib", potential_dir)
        
    if not os.path.exists(industry_path):
        return {"error": f"Industry '{industry}' not found"}
    
    bundle = {}
    integrity = {"components": {}, "master_hash": ""}
    file_map = {
        "standard_metrics.json": "standard_metrics", 
        "standard_data_rules.json": "standard_data_rules", 
        "ontology_graph.json": "ontology_graph", 
        "physical_data_map.json": "physical_data_map"
    }
    
    combo_string = ""
    for filename, key in file_map.items():
        file_path = os.path.join(industry_path, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    bundle[key] = data
                    f_hash = get_deterministic_json_hash(data)
                    integrity["components"][key] = f_hash
                    combo_string += f_hash
                except:
                    bundle[key] = []
                    integrity["components"][key] = "ERROR"
        else:
            bundle[key] = []
            integrity["components"][key] = "MISSING"

    integrity["master_hash"] = hashlib.sha256(combo_string.encode('utf-8')).hexdigest()
    bundle["integrity"] = integrity
    return bundle

@app.get("/agent/stream")
async def message_stream():
    """
    Streams the log file to the frontend via SSE.
    """
    async def event_generator():
        with open(LOG_FILE, "r") as f:
            # Go to end of file to start? No, we want to see history if we refresh.
            # But for "Live" feel, maybe we start at 0 and stream everything.
            f.seek(0, 0)
            while True:
                line = f.readline()
                if line:
                    yield {"data": line.strip()}
                else:
                    await asyncio.sleep(0.1)

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    # Clean logs on start
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
