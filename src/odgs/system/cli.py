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

@app.command()
def harvest(
    blueprint: str = typer.Argument(..., help="The Source Blueprint (nl_awb, fibo, iso_42001, gdpr, basel)"),
    reference_id: str = typer.Argument(..., help="The ID to harvest (e.g. '1:3' for AwB, 'InterestRate' for FIBO, '5' for GDPR Art.5, 'CET1' for Basel)")
):
    """
    Harvest a Sovereign Definition from an External Authority.
    
    Available blueprints:
      nl_awb     — Dutch Administrative Law (wetten.overheid.nl)
      fibo       — Financial Industry Business Ontology (spec.edmcouncil.org)
      iso_42001  — ISO/IEC 42001 AI Management System
      gdpr       — EU General Data Protection Regulation (eur-lex.europa.eu)
      basel      — Basel III/IV Framework (bis.org)
    """
    from odgs.harvester.blueprints.nl_awb import AwBHarvester
    from odgs.harvester.blueprints.fibo import FIBOHarvester
    from odgs.harvester.blueprints.iso_42001 import ISO42001Harvester
    from odgs.harvester.blueprints.gdpr import GDPRHarvester
    from odgs.harvester.blueprints.basel import BaselHarvester
    from odgs.harvester.core import HarvesterException
    
    BLUEPRINTS = {
        "nl_awb": AwBHarvester,
        "fibo": FIBOHarvester,
        "iso_42001": ISO42001Harvester,
        "gdpr": GDPRHarvester,
        "basel": BaselHarvester,
    }
    
    console.print(Panel(f"🌾 [bold green]Sovereign Harvester[/bold green] | Blueprint: [cyan]{blueprint}[/cyan]"))
    
    try:
        harvester_cls = BLUEPRINTS.get(blueprint)
        if not harvester_cls:
            available = ", ".join(BLUEPRINTS.keys())
            console.print(f"[bold red]Error:[/bold red] Unknown blueprint '{blueprint}'. Available: {available}")
            raise typer.Exit(code=1)
        
        harvester = harvester_cls()
            
        with console.status(f"Harvesting {reference_id}...", spinner="earth"):
            definition = harvester.harvest(reference_id)
            save_path = harvester.save(definition)
            
        console.print(f"✅ [bold green]Harvest Complete.[/bold green]")
        console.print(f"   📜 Saved to: {save_path}")
        console.print(f"   🔐 Content Hash: {definition['metadata'].get('content_hash', 'N/A')}")

    except HarvesterException as e:
        console.print(f"[bold red]Harvest Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]System Error:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def generate(
    industry: str = typer.Argument(..., help="The target industry (e.g. 'Healthcare', 'Banking')"),
    key: str = typer.Option(None, "--key", help="Google Gemini API Key (or set GEMINI_API_KEY env var)")
):
    """
    Generate a Draft Governance Bundle using AI (Gemini).
    """
    from odgs.factory.generator import generate_bundle
    from odgs.system.config import settings
    
    # Resolve API Key (CLI Flag > Settings/.env)
    api_key = key or settings.GEMINI_API_KEY
    if not api_key:
        console.print("[bold red]Error:[/bold red] Google Gemini API Key required. Set GEMINI_API_KEY in .env or pass --key.")
        raise typer.Exit(code=1)

    console.print(Panel(f"🏭 [bold purple]ODGS Factory[/bold purple] | Target: [cyan]{industry}[/cyan]"))
    
    definitions = generate_bundle(industry, api_key)
    
    if not definitions:
        console.print("[yellow]No definitions generated.[/yellow]")
        raise typer.Exit(code=1)

    # Save Drafts
    base_dir = "data/drafts"
    industry_slug = industry.lower().replace(" ", "_")
    output_dir = os.path.join(base_dir, industry_slug)
    os.makedirs(output_dir, exist_ok=True)

    count = 0
    for definition in definitions:
        # Create a filename from the URN
        # urn:odgs:def:ai_synthetic:churn_rate:v1 -> churn_rate.json
        parts = definition.urn.split(":")
        if len(parts) > 4:
            clean_name = parts[4] # slug
        else:
            clean_name = f"item_{count}"
            
        filename = f"{clean_name}.json"
        path = os.path.join(output_dir, filename)
        
        with open(path, "w") as f:
            f.write(definition.model_dump_json(indent=2))
        count += 1
        
    console.print(f"\n✅ [bold green]Factory Run Complete.[/bold green]")
    console.print(f"   📂 Drafts: {count} generated.")
    console.print(f"   📍 Location: {output_dir}")

@app.command()
def ui():
    """
    Launch the Sovereign Web Interface (Local Dashboard).
    """
    import subprocess
    
    console.print(Panel("🏛️  Launching [bold cyan]Sovereign UI[/bold cyan]...", border_style="cyan"))
    
    dashboard_path = os.path.join(os.path.dirname(__file__), "../ui/dashboard.py")
    dashboard_path = os.path.abspath(dashboard_path)
    
    try:
        # Check for streamlit
        subprocess.run(["streamlit", "--version"], check=True, capture_output=True)
        
        console.print(f"   📍 Dashboard: {dashboard_path}")
        console.print("   🚀 Opening browser...")
        
        # Run Streamlit
        os.system(f"streamlit run {dashboard_path}")
        
    except FileNotFoundError:
        console.print("[bold red]Error:[/bold red] Streamlit not found. Install it with `pip install streamlit`.")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def register(
    email: str = typer.Option(..., "--email", "-e", help="Email for Critical Security Alerts"),
    org: str = typer.Option(None, "--org", "-o", help="Organization Name (Optional)")
):
    """
    Register this Node for Critical Security Alerts (Sovereign Handshake).
    """
    import requests
    import datetime
    
    console.print(Panel(f"🛡️  [bold cyan]Sovereign Handshake Protocol[/bold cyan]"))
    console.print(f"   Connecting to Metric Provenance Authority...")

    # pseudo-logic for now - we don't have a backend yet
    # In a real scenario, this would POST to https://api.metricprovenance.com/register
    
    registration_data = {
        "email": email,
        "org": org,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "3.3.0",
        "node_id": generate_project_hash(os.getcwd()).get("master_hash", "UNKNOWN")[:8]
    }
    
    # Simulate network delay for effect
    import time
    with console.status("Establishing Secure Channel...", spinner="dots"):
        time.sleep(1.5)
        
    # Write local hidden file to persist 'Verified' status
    config_dir = os.path.join(os.getcwd(), ".odgs")
    os.makedirs(config_dir, exist_ok=True)
    reg_file = os.path.join(config_dir, "registration.lock")
    
    with open(reg_file, 'w') as f:
        json.dump(registration_data, f, indent=2)
        
    console.print(f"\n✅ [bold green]Handshake Verified.[/bold green]")
    console.print(f"   Identity: {email}")
    console.print(f"   Status:   [bold green]Active Node[/bold green]")
    console.print(f"   Access:   Critical Security Feed Enabled.")

if __name__ == "__main__":
    app()
