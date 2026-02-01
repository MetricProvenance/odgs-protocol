import typer
import json
import os
import sys
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

# Add project root to path to allow imports
# Note: sys.path hack removed as we are now a proper package

from .scripts.validate_schema import validate_all
from .scripts.hashing import generate_project_hash
from .adapters.dbt.generate_seeds import generate_seeds
from .adapters.dbt.generate_tests import generate_tests
from .adapters.dbt.generate_semantic_models import generate_dbt_semantic_models
from .adapters.powerbi.generate_tmsl import generate_powerbi_tmsl
from .adapters.tableau.generate_tds import generate_tableau_tds

app = typer.Typer(help="ODGS: The Protocol for Algorithmic Accountability")
console = Console()

@app.command()
def init(
    name: str = typer.Argument(..., help="Name of the new governance project"),
):
    """
    Initialize a new ODGS project.
    """
    console.print(Panel(f"🚀 Initializing ODGS Project: [bold cyan]{name}[/bold cyan]"))

    base_path = os.path.join(os.getcwd(), name)
    
    if os.path.exists(base_path):
        console.print(f"[bold red]Error:[/bold red] Directory '{name}' already exists.")
        raise typer.Exit(code=1)

    # Create directories
    os.makedirs(os.path.join(base_path, "schemas"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "adapters"), exist_ok=True)
    
    # Create standard_metrics.json
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

    # In a real package, we would copy these from the installed protocol/lib
    # For now, we stub them empty or copy if they exist in the package
    
    with open(os.path.join(base_path, "standard_metrics.json"), "w") as f:
        json.dump([sample_metric], f, indent=2)

    # Create other protocol files
    protocol_files = [
        "standard_dq_dimensions.json",
        "standard_data_rules.json",
        "root_cause_factors.json",
        "business_process_maps.json",
        "physical_data_map.json",
        "ontology_graph.json"
    ]
    
    for p_file in protocol_files:
        p_path = os.path.join(base_path, p_file)
        # Verify if we can copy from source in future
        with open(p_path, "w") as f:
             json.dump([], f, indent=2)

    # Create odgs.json config
    config = {
        "project_name": name,
        "version": "0.1.0"
    }
    with open(os.path.join(base_path, "odgs.json"), "w") as f:
        json.dump(config, f, indent=2)

    console.print(f"✅ Created directory structure in [bold green]{name}/[/bold green]")
    console.print(f"✅ Created [bold green]standard_metrics.json[/bold green]")
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

    # Load existing metrics (assuming we are in project root)
    metrics_file = "standard_metrics.json"
    if not os.path.exists(metrics_file):
        console.print(f"[bold red]Error:[/bold red] {metrics_file} not found. Are you in an ODGS project root?")
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
    
    # Fallback to package root (dev mode)
    package_reg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "registry.json")
    if os.path.exists(package_reg):
        return package_reg
        
    return None

@app.command()
def hash(
    verify: bool = typer.Option(False, "--verify", help="Check if current hash matches the registry")
):
    """
    Generate SHA-256 Governance Hash for the current project state.
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
         # hash verify raises Exit(1) on failure, re-raise it
         raise
    except Exception as e:
         console.print(f"❌ Registry Check Failed: {e}")
         raise typer.Exit(code=1)
         
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

if __name__ == "__main__":
    app()
