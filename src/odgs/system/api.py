from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import subprocess
import os
import sys
import hashlib
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import json

from pydantic import BaseModel

class InterceptRequest(BaseModel):
    process_urn: str
    data_context: Dict[str, Any]
    integrity_hash: Optional[str] = None  # Optional in Trust Mode, Mandatory in Strict Mode

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

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables
load_dotenv(os.path.join(project_root, ".env"))

from pydantic import BaseModel
from odgs.system.scripts.agent_logic import generate_with_gemini, write_bundle, run_agent_chat
from odgs.executive.interceptor import OdgsInterceptor
from odgs.system.scripts.hashing import get_deterministic_json_hash

class ChatRequest(BaseModel):
    prompt: str
    industry: str = None

# ... (rest of imports)

@app.get("/api/protocol/core")
async def get_core_protocol():
    """
    Returns the foundational definitions (DQ Dimensions, Root Causes) from Sovereign Planes.
    """
    # Map to new Sovereign Structure
    core_files = {
        "dq_dimensions": "legislative/standard_dq_dimensions.json",
        "root_causes": "judiciary/root_cause_factors.json",
        "business_processes": "executive/business_process_maps.json",
        "physical_map": "executive/physical_data_map.json",
        "ontology": "legislative/ontology_graph.json",
        "rules": "judiciary/standard_data_rules.json",
        "metrics": "legislative/standard_metrics.json"
    }
    
    response = {}
    for key, rel_path in core_files.items():
        try:
            full_path = os.path.join(project_root, rel_path)
            with open(full_path, "r") as f:
                response[key] = json.load(f)
        except Exception:
             response[key] = []
             
    return response

@app.post("/api/agent/chat")
async def agent_chat(request: ChatRequest):
    """
    Interactive chat with the ODGS Agent.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    industry_dir = f"protocol/lib/{request.industry.lower().replace(' ', '_')}" if request.industry else None
    
    files = []
    
    # 1. Load Industry Specifics if requested
    if industry_dir and os.path.exists(industry_dir):
        files.extend([
            os.path.join(industry_dir, "standard_metrics.json"),
            os.path.join(industry_dir, "standard_data_rules.json"),
            os.path.join(industry_dir, "ontology_graph.json"),
            os.path.join(industry_dir, "physical_data_map.json")
        ])
    
    # 2. Load Global Reference from Sovereign Planes
    files.extend([
        os.path.join(project_root, "legislative", "standard_dq_dimensions.json"),
        os.path.join(project_root, "judiciary", "root_cause_factors.json"),
        os.path.join(project_root, "executive", "business_process_maps.json")
    ])
    
    response = run_agent_chat(request.prompt, files, api_key)
    return {"response": response}

@app.get("/api/agent/audit/{industry}")
async def agent_audit(industry: str):
    """
    Run an AI semantic audit on a specific industry bundle.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    industry_dir = f"protocol/lib/{industry.lower().replace(' ', '_')}"
    global_dir = "protocol/lib"
    
    files = [
        os.path.join(industry_dir, "standard_metrics.json"),
        os.path.join(industry_dir, "standard_data_rules.json"),
        os.path.join(global_dir, "standard_dq_dimensions.json")
    ]
    
    prompt = "Perform a deep semantic audit. Look for logic errors, missing fields, and EU AI Act risks."
    response = run_agent_chat(prompt, files, api_key)
    return {"audit_report": response}

@app.get("/api/protocol/library")
async def get_library():
    """
    Returns list of available industry bundles.
    """
    lib_path = os.path.join(project_root, "protocol", "lib")
    if not os.path.exists(lib_path):
        return []
    
    bundles = []
    for item in os.listdir(lib_path):
        if os.path.isdir(os.path.join(lib_path, item)):
            bundles.append(item.replace("_", " ").title())
    return bundles

@app.get("/api/protocol/bundle/{industry}")
async def get_bundle(industry: str):
    """
    Returns the specific industry bundle (Metrics, Rules, Ontology).
    """
    # Sanitize and format
    slug = industry.lower().replace(" ", "_")
    bundle_path = os.path.join(project_root, "protocol", "lib", slug)
    
    if not os.path.exists(bundle_path):
        raise HTTPException(status_code=404, detail=f"Bundle '{industry}' not found")
        
    response = {}
    files = {
        "standard_metrics": "standard_metrics.json",
        "standard_data_rules": "standard_data_rules.json",
        "ontology_graph": "ontology_graph.json",
        "physical_data_map": "physical_data_map.json"
    }
    
    for key, filename in files.items():
        try:
            with open(os.path.join(bundle_path, filename), "r") as f:
                response[key] = json.load(f)
        except Exception:
            response[key] = []
            
    return response

# Logger to duplicate stdout to both terminal and log file immediately
class Logger(object):
    def __init__(self, original_stdout, log_file):
        self.terminal = original_stdout
        self.log_file = log_file

    def write(self, message):
        self.terminal.write(message)
        try:
            with open(self.log_file, "a") as f:
                f.write(message)
                f.flush()
        except Exception:
            pass

    def flush(self):
        self.terminal.flush()

# Helper to capture stdout/print from agent logic and write to log file
def run_generation_task(industry: str):
    import io
    import datetime
    
    # Save original stdout
    original_stdout = sys.stdout
    
    # Use the MAIN audit log for visibility
    audit_log_path = os.path.join(project_root, "sovereign_audit.log")
    
    # Create Tee logger
    logger = Logger(original_stdout, audit_log_path)
    
    try:
        # Redirect stdout to our Tee logger
        sys.stdout = logger
        
        # Write start marker
        # We use a simple format that the frontend terminal can display
        print(f"\n--- AGENT SESSION START: {industry} [{datetime.datetime.now().isoformat()}] ---\n")
            
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Error: GEMINI_API_KEY not found in environment.")
            return

        print(f"🤖 Agent Directives Received: {industry}")
        data = generate_with_gemini(industry, api_key)
        
        if data:
            print("💾 Saving Bundle to filesystem...")
            slug = industry.lower().replace(" ", "_")
            output_dir = os.path.join(project_root, "protocol", "lib", slug)
            write_bundle(data, output_dir)
            print("✨ Task Complete. Bundle deployed to Library.")
        else:
            print("❌ Generation failed to produce data.")

    except Exception as e:
        # Catch unexpected errors in the wrapper
        print(f"❌ Critical Error: {str(e)}\n")
             
    finally:
        # Restore original stdout
        sys.stdout = original_stdout


@app.post("/agent/generate")
async def generate_agent(industry: str, background_tasks: BackgroundTasks):
    """
    Triggers the AI Agent to generate a new governance bundle.
    """
    background_tasks.add_task(run_generation_task, industry)
    return {"status": "started", "message": f"Agent assigned to sector: {industry}"}

@app.get("/agent/stream")
async def stream_logs(request: Request):
    """
    Streams agent activity logs to the frontend via SSE.
    """
    # Use the SOVEREIGN log file (sovereign_audit.log)
    audit_log_path = os.path.join(project_root, "sovereign_audit.log")

    async def event_generator():
        last_pos = 0
        if os.path.exists(audit_log_path):
             # For demo, maybe show the last 1KB so they see immediate context?
             # Or start at 0 to show full history of this session.
             # Let's start at filesiez for specific "tail" behavior or 0 for full.
             # Frontend uses slice(-19) so sending full file is okay-ish but inefficient if huge.
             # Let's send only new data effectively.
             # But if user refreshes, they might want last logs.
             # Simple approach: Start from 0 (history)
             last_pos = 0 

        while True:
            if await request.is_disconnected():
                break
                
            if os.path.exists(audit_log_path):
                with open(audit_log_path, "r") as f:
                    f.seek(last_pos)
                    new_data = f.read()
                    if new_data:
                        last_pos = f.tell()
                        for line in new_data.splitlines():
                            if line.strip():
                                yield {"data": line.strip()}
            
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())

# --- SOVEREIGN ENDPOINTS (ARTICLE 10 & 12) ---

from odgs.executive.interceptor import OdgsInterceptor, ProcessBlockedException, SecurityException
from odgs.system.scripts.hashing import generate_project_hash

class InterceptRequest(BaseModel):
    process_urn: str
    data_context: Dict[str, Any]
    integrity_hash: Optional[str] = None  # Optional in Trust Mode, Mandatory in Strict Mode

@app.post("/api/sovereign/intercept")
async def intercept_process(req: InterceptRequest):
    """
    Sovereign Interceptor Endpoint.
    Propagates Hard Stops and Security Exceptions to the Frontend.
    """
    try:
        # Initialize Interceptor (auto-locates root)
        interceptor = OdgsInterceptor()
        
        # Execute Interception
        interceptor.intercept(req.process_urn, req.data_context, required_integrity_hash=req.integrity_hash)
        
        return {
            "status": "GRANTED",
            "message": "Access Granted. Semantic Checks Passed."
        }

    except SecurityException as e:
        # 403 Forbidden for Security/Hash Failures
        return {
            "status": "BLOCKED",
            "reason": "SECURITY_EXCEPTION",
            "message": str(e)
        }
    except ProcessBlockedException as e:
        # 400 Bad Request for Rule Violations (Business Logic)
        return {
            "status": "BLOCKED",
            "reason": "RULE_VIOLATION",
            "message": str(e)
        }
    except Exception as e:
        # 500 for unexpected system errors
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sovereign/hash")
async def get_sovereign_hash():
    """
    Generates and returns the authoritative 'Passport' hash.
    Used by the frontend 'Strict Mode' to prove identity.
    """
    try:
        result = generate_project_hash(project_root)
        return {"master_hash": result["master_hash"]}
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to generate hash: {e}")

@app.get("/api/sovereign/logs")
async def get_audit_logs():
    """
    Retrieves the immutable audit logs (Article 12).
    """
    log_path = os.path.join(project_root, "sovereign_audit.log")
    if not os.path.exists(log_path):
        return {"logs": []}
    
    try:
        with open(log_path, 'r') as f:
            # Read last 50 lines, parse JSON if possible, otherwise string
            lines = f.readlines()[-50:]
            parsed_logs = []
            for line in reversed(lines):
                 try:
                     parts = line.split(" - ", 1)
                     if len(parts) > 1:
                         json_part = parts[1]
                         parsed_logs.append(json.loads(json_part))
                 except:
                     pass # Skip malformed lines
            return {"logs": parsed_logs}
    except Exception as e:
        return {"logs": [], "error": str(e)}

from odgs.system.scripts.fabricator import fabricate_data_context

@app.get("/api/sovereign/fabricate")
async def fabricate_data(scenario: str = "valid"):
    """
    Returns synthetic data for the demo.
    Scenarios: 'valid', 'invalid_format'
    """
    try:
        data = fabricate_data_context(scenario)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    # Truncate or create log on start
    with open(LOG_FILE, "w") as f:
        f.write("[System] Agent Initialized. Waiting for Directive...\n")
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
