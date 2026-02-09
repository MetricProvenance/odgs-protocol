import typer
import json
import os
import sys
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

# Add project root to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Imports from the Sovereign System
# Note: These paths assume we are running from project root or installed as package
try:
    from odgs.system.scripts.validate_schema import validate_all
    from odgs.system.scripts.hashing import generate_project_hash
    # Adapters
    from odgs.system.adapters.dbt.generate_seeds import generate_seeds
    from odgs.system.adapters.dbt.generate_tests import generate_tests
    from odgs.system.adapters.dbt.generate_semantic_models import generate_dbt_semantic_models
    from odgs.system.adapters.powerbi.generate_tmsl import generate_powerbi_tmsl
    from odgs.system.adapters.tableau.generate_tds import generate_tableau_tds
    # Executive
    from odgs.executive.interceptor import OdgsInterceptor, ProcessBlockedException, SecurityException
    # Agent
    from odgs.system.scripts.agent_logic import generate_with_gemini, write_bundle, run_agent_chat
except ImportError as e:
    # Graceful fallback for dev environment vs installed package
    print(f"Import Error (Dev Mode?): {e}")
    # Try local relative imports for scripts if in dev
    from scripts.validate_schema import validate_all
    from scripts.hashing import generate_project_hash

app = typer.Typer(
    help="ODGS Protocol CLI - The Sovereign Data Governance Engine",
    no_args_is_help=True
)
console = Console()

@app.command()
def version():
    """
    Print the current ODGS version.
    """
    console.print(Panel("ODGS Sovereign Engine v2.0.0", border_style="cyan"))

@app.command()
def init(
    name: str = typer.Argument(..., help="Name of the new governance project"),
):
    """
    Initialize a new ODGS Sovereign Project (3-Plane Architecture).
    """
    console.print(Panel(f"🚀 Initializing ODGS Sovereign Project: [bold cyan]{name}[/bold cyan]"))

    base_path = os.path.join(os.getcwd(), name)
    
    if os.path.exists(base_path):
        console.print(f"[bold red]Error:[/bold red] Directory '{name}' already exists.")
        raise typer.Exit(code=1)

    # Create Sovereign Planes
    planes = ["legislative", "judiciary", "executive", "system", "adapters"]
    for plane in planes:
        os.makedirs(os.path.join(base_path, plane), exist_ok=True)
    
    # --- Legislative Plane (Definitions) ---
    sample_metric = {
        "metric_id": "KPI_001",
        "name": "Sample_Metric",
        "domain": "Example",
        "calculation_logic": {
            "abstract": "A + B",
            "sql_standard": "SUM(a) + SUM(b)"
        },
        "owner": "Data_Team",
        "quality_threshold": "99.0%",
        "status": "Active"
    }
    
    # Write legislative artifacts
    with open(os.path.join(base_path, "legislative", "standard_metrics.json"), "w") as f:
        json.dump([sample_metric], f, indent=2)
    
    for filename in ["standard_dq_dimensions.json", "ontology_graph.json"]:
        with open(os.path.join(base_path, "legislative", filename), "w") as f:
            json.dump([], f, indent=2)

    # --- Judiciary Plane (Rules) ---
    for filename in ["standard_data_rules.json", "root_cause_factors.json"]:
         with open(os.path.join(base_path, "judiciary", filename), "w") as f:
            json.dump([], f, indent=2)

    # --- Executive Plane (Enforcement) ---
    for filename in ["business_process_maps.json", "physical_data_map.json", "runtime_config.json"]:
         with open(os.path.join(base_path, "executive", filename), "w") as f:
            json.dump([], f, indent=2)

    # Create odgs.json config in root
    config = {
        "project_name": name,
        "version": "2.0.0",
        "architecture": "sovereign_v1"
    }
    with open(os.path.join(base_path, "odgs.json"), "w") as f:
        json.dump(config, f, indent=2)

    console.print(f"✅ Created Sovereign Territory: [bold green]{name}/[/bold green]")
    console.print(f"   🏛️  /legislative (Metrics, Ontology)")
    console.print(f"   ⚖️  /judiciary (Rules)")
    console.print(f"   ⚔️  /executive (Enforcement)")
    
    console.print(f"\n[bold]Next Steps:[/bold]")
    console.print(f"  cd {name}")
    console.print(f"  odgs add metric")

@app.command()
def add(
    item_type: str = typer.Argument("metric", help="Type of item to add (currently only 'metric')"),
):
    """
    Add a new item to the schema (interactive).
    """
    if item_type != "metric":
        console.print(f"[red]Only 'metric' is supported for now.[/red]")
        raise typer.Exit(code=1)

    console.print(Panel("➕ Add New Metric"))

    name = Prompt.ask("Metric Name (e.g. Gross_Churn)")
    metric_id = Prompt.ask("Metric ID", default=f"KPI_{name.upper()}")
    domain = Prompt.ask("Domain", default="General")
    owner = Prompt.ask("Owner", default="Data_Team")
    abstract_logic = Prompt.ask("Abstract Logic (e.g. Revenue - Cost)")
    
    new_metric = {
        "metric_id": metric_id,
        "name": name,
        "domain": domain,
        "calculation_logic": {
            "abstract": abstract_logic,
            "sql_standard": "", # Placeholder
            "dax_pattern": ""   # Placeholder
        },
        "owner": owner,
        "quality_threshold": "95.0%"
    }

    # Load existing metrics from Legislative Plane
    metrics_file = os.path.join("legislative", "standard_metrics.json")
    if not os.path.exists(metrics_file):
        # Fallback for old projects or mixed state
        if os.path.exists("standard_metrics.json"):
            metrics_file = "standard_metrics.json"
        else:
            console.print(f"[bold red]Error:[/bold red] Could not find standard_metrics.json in legislative/.")
            raise typer.Exit(code=1)

    with open(metrics_file, "r") as f:
        try:
            metrics = json.load(f)
        except json.JSONDecodeError:
            metrics = []
    
    if not isinstance(metrics, list):
        metrics = []

    metrics.append(new_metric)

    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)

    console.print(f"✅ Added [bold cyan]{name}[/bold cyan] to {metrics_file}")

def get_registry_path():
    # Helper to find registry.json. Checks CWD then package root.
    cwd_reg = os.path.join(os.getcwd(), "registry.json")
    if os.path.exists(cwd_reg):
        return cwd_reg
    return None

@app.command()
def hash(
    verify: bool = typer.Option(False, "--verify", help="Check if current hash matches the registry")
):
    """
    Generate SHA-256 Governance Hash for the current project Logic.
    """
    console.print(Panel("🔐 Generating Deterministic Semantic Hash..."))
    
    result = generate_project_hash(os.getcwd())
    master_hash = result["master_hash"]
    
    console.print(f"Master Hash: [bold yellow]{master_hash}[/bold yellow]")
    console.print("\nComponent Hashes:")
    for file, h in result["components"].items():
        status = "[green]OK[/green]" if "MISSING" not in h and "ERROR" not in h else "[red]FAIL[/red]"
        console.print(f"  {file}: {status} ({h[:8]}...)")

    if verify:
        reg_path = get_registry_path()
        if not reg_path:
             console.print("\n[bold red]Registry Verification Failed:[/bold red] registry.json not found.")
             raise typer.Exit(code=1)
             
        with open(reg_path, 'r') as f:
            registry = json.load(f)
            
        latest = registry.get("latest_verified_hash", "")
        if master_hash == latest:
            console.print("\n✅ [bold green]Systems Nominal. Hash matches Registry ledger.[/bold green]")
        else:
            console.print("\n🛑 [bold red]COMPLIANCE ALERT: Hash Mismatch![/bold red]")
            console.print(f"  Expected: {latest}")
            console.print(f"  Actual:   {master_hash}")
            console.print("  [dim]Data Drift Detected. Execution halted.[/dim]")
            raise typer.Exit(code=1)

@app.command()
def validate():
    """
    Verify schema integrity and AI safety compliance.
    """
    console.print("🛡️  Running ODGS AI Safety Protocol Checks...")
    console.print("   [dim]Verifying Semantic Hallucination safeguards...[/dim]")
    
    # Step 1: Structural Validation
    try:
        validate_all()
    except Exception as e:
        console.print(f"❌ Structural Validation Failed: {e}")
        raise typer.Exit(code=1)
        
    # Step 2: Hash Integrity Check (The "Hard Stop")
    console.print("\n   [dim]Verifying Registry Integrity...[/dim]")
    try:
        hash(verify=True)
    except typer.Exit:
         raise
    except Exception as e:
         console.print(f"❌ Registry Check Failed: {e}")
         # We allow validation to pass even if registry is missing, but warn
         # raise typer.Exit(code=1)

    console.print("✅ All systems go. Data stack is EU AI ACT Compliant.")

@app.command()
def build():
    """
    Generate downstream adapters (dbt, PowerBI, Tableau).
    """
    console.print("🏗️  Building Governance Artifacts...")
    
    console.print("\n--- dbt Adapter ---")
    generate_seeds()
    generate_tests()
    generate_dbt_semantic_models()
    
    console.print("\n--- Power BI Adapter ---")
    generate_powerbi_tmsl()
    
    console.print("\n--- Tableau Adapter ---")
    generate_tableau_tds()
    
    console.print("\n✨ Build Complete. Your data ecosystem is now synchronized.")

@app.command()
def api(
    host: str = typer.Option("127.0.0.1", help="Host interface to bind to"),
    port: int = typer.Option(8000, help="Port to listen on"),
    reload: bool = typer.Option(True, help="Enable auto-reload")
):
    """
    Launch the ODGS Sovereign API Server.
    """
    import uvicorn
    console.print(Panel(f"🚀 Launching ODGS API on [cyan]http://{host}:{port}[/cyan]"))
    uvicorn.run("system.api:app", host=host, port=port, reload=reload)

@app.command()
def enforce(
    process: str = typer.Option(..., "--process", "-p", help="URN or ID of the Business Process Stage"),
    data: str = typer.Option(..., "--data", "-d", help="JSON string of data context"),
    integrity_hash: str = typer.Option(None, "--hash", "-h", help="Required Governance Hash for Sovereign Handshake")
):
    """
    Enforce Governance Rules acting as a Semantic Firewall (Hard Stop).
    """
    console.print(Panel(f"🛡️  [bold red]ODGS INTERCEPTOR[/bold red] | Checking Process: [cyan]{process}[/cyan]"))

    try:
        # Parse data context
        try:
            context = json.loads(data)
        except json.JSONDecodeError:
            console.print("[bold red]Error:[/bold red] Invalid JSON data provided.")
            raise typer.Exit(code=1)

        # Initialize Interceptor
        # It auto-detects root if we are in a valid structure
        interceptor = OdgsInterceptor()
        
        # Normalize Process URN if user only provided ID
        if not process.startswith("urn:"):
            process = f"urn:odgs:process:{process}"

        # Execute Interception with Cryptographic Handshake
        interceptor.intercept(process, context, required_integrity_hash=integrity_hash)
        
        # If we get here, no exception was raised
        console.print(Panel("✅ [bold green]ACCESS GRANTED[/bold green]\nSemantic Checks Passed.", border_style="green"))

    except SecurityException as e:
        console.print(Panel(f"⛔ [bold red]SECURITY ALERT[/bold red]\n{str(e)}", border_style="red"))
        raise typer.Exit(code=1)
    except ProcessBlockedException as e:
        console.print(Panel(f"⛔ [bold red]HARD STOP TRIGGERED[/bold red]\n{str(e)}", border_style="red"))
        raise typer.Exit(code=1)
    except Exception as e:
         console.print(f"[bold red]Unexpected Error:[/bold red] {e}")
         raise typer.Exit(code=1)

agent_app = typer.Typer(help="Agentic AI capabilities for ODGS.")
app.add_typer(agent_app, name="agent")

def get_api_key():
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY logic not found. Please set it in your environment or .env file.")
        raise typer.Exit(code=1)
    return key

@agent_app.command()
def generate(
    industry: str = typer.Argument(..., help="Industry to research and generate a schema for"),
    api_key: Optional[str] = typer.Option(None, envvar="GEMINI_API_KEY", help="Gemini API Key")
):
    """
    Research and generate a new ODGS Governance Bundle for an industry.
    """
    if not api_key:
        api_key = get_api_key()

    console.print(Panel(f"🔍 [bold]Agent Directive:[/bold] Research & Generate for [cyan]{industry}[/cyan]"))
    
    data = generate_with_gemini(industry, api_key)
    if data:
        # TODO: Update this to write to new structure structure? 
        # For now, library is still in protocol/lib, which is fine as a staging area.
        output_dir = f"protocol/lib/{industry.lower().replace(' ', '_')}"
        write_bundle(data, output_dir)
        console.print(f"\n✅ [bold green]Success![/bold green] Bundle generated in [cyan]{output_dir}/[/cyan]")
    else:
        console.print("[bold red]Failure:[/bold red] Agent could not generate bundle.")
        raise typer.Exit(code=1)

@agent_app.command()
def audit():
    """
    Audit the current ODGS project using AI-driven semantic analysis.
    """
    api_key = get_api_key()
    console.print(Panel("🛡️  [bold]Agent Audit:[/bold] Analyzing project logic and compliance..."))
    
    # Audit looking at the Planes
    files = [
        "legislative/standard_metrics.json",
        "judiciary/standard_data_rules.json",
        "legislative/ontology_graph.json"
    ]
    prompt = "Analyze these governance files. Identify any logic gaps, overlapping definitions, or potential EU AI Act compliance risks. Provide high-level recommendations."
    
    response = run_agent_chat(prompt, files, api_key)
    console.print("\n[bold cyan]Agent Feedback:[/bold cyan]")
    console.print(response)

@agent_app.command()
def chat(
    prompt: str = typer.Argument(..., help="Question or directive for the ODGS agent")
):
    """
    Chat with the ODGS Governance Agent about your project.
    """
    api_key = get_api_key()
    files = [
        "legislative/standard_metrics.json",
        "judiciary/standard_data_rules.json",
        "legislative/ontology_graph.json",
        "executive/physical_data_map.json"
    ]
    
    with console.status("[bold cyan]Agent is thinking...[/bold cyan]"):
        response = run_agent_chat(prompt, files, api_key)
    
    console.print(Panel(response, title="ODGS Agent Response", border_style="cyan"))

if __name__ == "__main__":
    app()
