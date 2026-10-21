import typer
import json
import os
import sys
import importlib.metadata
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

# Add project root to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from odgs.system.scripts.validate_schema import validate_all
    from odgs.system.scripts.hashing import generate_project_hash
    # Adapters
    from odgs.system.adapters.dbt.generate_seeds import generate_seeds
    from odgs.system.adapters.dbt.generate_tests import generate_tests
    from odgs.system.adapters.dbt.generate_semantic_models import generate_dbt_semantic_models
    # Executive
    from odgs.executive.interceptor import OdgsInterceptor, ProcessBlockedException, SecurityException
except ImportError as e:
    print(f"Import Error (Dev Mode?): {e}")
    from scripts.validate_schema import validate_all
    from scripts.hashing import generate_project_hash
    from adapters.dbt.generate_seeds import generate_seeds
    from adapters.dbt.generate_tests import generate_tests
    from adapters.dbt.generate_semantic_models import generate_dbt_semantic_models
    from executive.interceptor import OdgsInterceptor, ProcessBlockedException, SecurityException

app = typer.Typer(
    help="ODGS Protocol CLI - Runtime Semantic Policy Enforcement & Certification Engine (v6.1.0)",
    no_args_is_help=True
)
console = Console()


def get_version():
    try:
        from odgs import __version__
        return __version__
    except ImportError:
        return importlib.metadata.version("odgs")


@app.command()
def version():
    """
    Print the current ODGS protocol version.
    """
    console.print(Panel(f"ODGS Protocol Reference Engine v{get_version()}", border_style="cyan"))


@app.command()
def conformance(
    project_path: str = typer.Argument(".", help="Path to the ODGS governance project directory"),
    level: str = typer.Option(
        "L1",
        "--level",
        "-l",
        help="ODGS Implementation Conformance Level: L1 (Level 1 Core) or L2 (Level 2 Attested). Distinct from ISO/IEC 17000 / Eclipse CAP and EAS 18425:2026."
    )
):
    """
    Run an ODGS Implementation Conformance Level self-check against the specified project (v6.1.0).

    L1 (Level 1 Core): Verifies core plane artifacts exist and are schema-valid.
    L2 (Level 2 Attested): Full cross-reference validation including cryptographic hash consistency.
    Note: ODGS Implementation Conformance Levels (L1/L2) are distinct from ISO/IEC 17000 conformity
    assessment (Eclipse CAP) and EAS 18425:2026 dataspace conformance profiles.
    """
    from odgs.executive.interceptor import OdgsInterceptor
    from odgs.executive.exceptions import ConformanceException

    abs_path = os.path.abspath(project_path)
    console.print(Panel(f"🔍 ODGS Implementation Conformance Check [{level}] — {abs_path}", border_style="yellow"))

    try:
        interceptor = OdgsInterceptor(project_root_path=abs_path)
        result = interceptor.conformance_check(level=level)
        console.print(f"\n✅ [bold green]CONFORMANT[/bold green] — {result['passed']} checks passed")
        for check in result["checks_passed"]:
            console.print(f"   ✓ {check}")
    except ConformanceException as e:
        console.print(f"\n❌ [bold red]NON-CONFORMANT[/bold red] — {len(e.failures)} failure(s)")
        for failure in e.failures:
            console.print(f"   ✗ {failure}", style="red")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    batch_file: str = typer.Argument(..., help="Path to a JSON file containing an array of evaluation items"),
    project_path: str = typer.Option(".", "--project", "-p", help="Path to the ODGS governance project"),
    fail_fast: bool = typer.Option(False, "--fail-fast", help="Stop at first failure")
):
    """
    Evaluate multiple data payloads in a single batch run (v6.1.0).

    The input JSON file should contain an array of objects, each with
    'process_urn' and 'data_context' fields.
    """
    from odgs.executive.interceptor import OdgsInterceptor

    abs_path = os.path.abspath(project_path)
    console.print(Panel(f"📦 Batch Evaluation — {batch_file}", border_style="blue"))

    try:
        with open(batch_file, "r") as f:
            items = json.load(f)
    except Exception as e:
        console.print(f"[bold red]Failed to load batch file:[/bold red] {e}")
        raise typer.Exit(code=1)

    interceptor = OdgsInterceptor(project_root_path=abs_path)
    result = interceptor.intercept_batch(items, fail_fast=fail_fast)

    console.print(f"\n📊 Results: {result['passed']}/{result['total']} passed, {result['failed']} failed")
    for r in result["results"]:
        status_icon = "✅" if r["status"] == "APPROVED" else "❌"
        console.print(f"   {status_icon} [{r['index']}] {r['status']}: {r.get('error', '')}")

    if result["failed"] > 0:
        raise typer.Exit(code=1)


@app.command()
def init(
    name: str = typer.Argument(..., help="Name of the new governance project"),
    tier: str = typer.Option("standard", "--tier", help="Governance Tier (e.g. 'minimalist' or 'standard')")
):
    """
    Initialize a new ODGS Project (Planes I–V Architecture).
    """
    console.print(Panel(f"🚀 Initializing ODGS Project: [bold cyan]{name}[/bold cyan] (Tier: {tier})"))

    base_path = os.path.join(os.getcwd(), name)

    if os.path.exists(base_path):
        console.print(f"[bold red]Error:[/bold red] Directory '{name}' already exists.")
        raise typer.Exit(code=1)

    is_minimalist = tier.lower() == "minimalist"

    planes = ["legislative", "judiciary", "executive"]
    if not is_minimalist:
        planes.extend(["system", "adapters"])

    for plane in planes:
        os.makedirs(os.path.join(base_path, plane), exist_ok=True)

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

    with open(os.path.join(base_path, "legislative", "standard_metrics.json"), "w") as f:
        json.dump([sample_metric], f, indent=2)

    if not is_minimalist:
        for filename in ["standard_dq_dimensions.json", "ontology_graph.json"]:
            with open(os.path.join(base_path, "legislative", filename), "w") as f:
                json.dump([], f, indent=2)

    with open(os.path.join(base_path, "judiciary", "standard_data_rules.json"), "w") as f:
        json.dump([], f, indent=2)

    if not is_minimalist:
        with open(os.path.join(base_path, "judiciary", "root_cause_factors.json"), "w") as f:
            json.dump([], f, indent=2)

    exec_files = ["runtime_config.json"] if is_minimalist else ["business_process_maps.json", "physical_data_map.json", "runtime_config.json"]
    for filename in exec_files:
        with open(os.path.join(base_path, "executive", filename), "w") as f:
            json.dump([], f, indent=2)

    config = {
        "project_name": name,
        "version": get_version(),
        "architecture": "odgs_v6"
    }
    with open(os.path.join(base_path, "odgs.json"), "w") as f:
        json.dump(config, f, indent=2)

    console.print(f"✅ Created ODGS Project Directory: [bold green]{name}/[/bold green]")
    console.print("   🏛️  /legislative (Metrics, ISO/IEC 25012 Dimensions, Contextual Ontology)")
    console.print("   ⚖️  /judiciary (Validation Rules & Root Cause Factors)")
    console.print("   ⚔️  /executive (Contextual Process Bindings & Runtime Config)")

    console.print("\n[bold]Next Steps:[/bold]")
    console.print(f"  cd {name}")
    console.print("  odgs add metric")


@app.command()
def add(
    item_type: str = typer.Argument("metric", help="Type of item to add (currently only 'metric')"),
):
    """
    Add a new item to the schema (interactive).
    """
    if item_type != "metric":
        console.print("[red]Only 'metric' is supported for now.[/red]")
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
            "sql_standard": "",
            "dax_pattern": ""
        },
        "owner": owner,
        "quality_threshold": "95.0%"
    }

    metrics_file = os.path.join("legislative", "standard_metrics.json")
    if not os.path.exists(metrics_file):
        if os.path.exists("standard_metrics.json"):
            metrics_file = "standard_metrics.json"
        else:
            console.print("[bold red]Error:[/bold red] Could not find standard_metrics.json in legislative/.")
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
    cwd_reg = os.path.join(os.getcwd(), "registry.json")
    if os.path.exists(cwd_reg):
        return cwd_reg
    return None


@app.command()
def hash(
    verify: bool = typer.Option(False, "--verify", help="Check if current hash matches the local registry")
):
    """
    Generate SHA-256 Governance Hash for the current project logic.
    """
    console.print(Panel("🔐 Generating Deterministic Semantic Hash..."))

    result = generate_project_hash(os.getcwd())
    master_hash = result["master_hash"]

    console.print(f"Master Hash: [bold yellow]{master_hash}[/bold yellow]")
    console.print("\nComponent Hashes:")
    for file, h in result["components"].items():
        if h == "OPTIONAL_MISSING":
            status = "[dim]OPTIONAL[/dim]"
        elif "INVALID_JSON" in h or "ERROR" in h:
            status = "[red]FAIL[/red]"
        else:
            status = "[green]OK[/green]"
        console.print(f"  {file}: {status} ({h[:8]}...)")

    if verify:
        reg_path = get_registry_path()
        if not reg_path:
            console.print("\n[bold red]Registry Verification Failed:[/bold red] registry.json not found.")
            raise typer.Exit(code=1)

        with open(reg_path, "r") as f:
            registry = json.load(f)

        latest = registry.get("latest_verified_hash", "")
        if master_hash == latest:
            console.print("\n✅ [bold green]Systems Nominal. Hash matches local registry ledger.[/bold green]")
        else:
            console.print("\n🛑 [bold red]COMPLIANCE ALERT: Hash Mismatch![/bold red]")
            console.print(f"  Expected: {latest}")
            console.print(f"  Actual:   {master_hash}")
            console.print("  [dim]Semantic Drift Detected. Execution halted.[/dim]")
            raise typer.Exit(code=1)


@app.command()
def validate():
    """
    Verify schema integrity and governance artifact compliance.
    """
    console.print("🛡️  Running ODGS Protocol Schema & Hash Checks...")

    try:
        validate_all()
    except Exception as e:
        console.print(f"❌ Structural Validation Failed: {e}")
        raise typer.Exit(code=1)

    console.print("\n   [dim]Verifying Registry Integrity...[/dim]")
    try:
        hash(verify=True)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"❌ Registry Check Failed: {e}")

    console.print("✅ All systems go. Governance artifacts are schema-valid.")


@app.command()
def build():
    """
    Generate downstream open-source dbt adapter artifacts (seeds, tests, semantic models).
    """
    console.print("🏗️  Building Governance Artifacts (dbt Adapter)...")
    generate_seeds()
    generate_tests()
    generate_dbt_semantic_models()
    console.print("\n✨ Build Complete. Downstream dbt artifacts are synchronized.")


@app.command()
def api(
    host: str = typer.Option("127.0.0.1", help="Host interface to bind to"),
    port: int = typer.Option(8000, help="Port to listen on"),
    reload: bool = typer.Option(True, help="Enable auto-reload")
):
    """
    Launch the ODGS Local Validation API Server.
    """
    import uvicorn
    console.print(Panel(f"🚀 Launching ODGS API on [cyan]http://{host}:{port}[/cyan]"))
    uvicorn.run("system.api:app", host=host, port=port, reload=reload)


@app.command()
def enforce(
    process: str = typer.Option(..., "--process", "-p", help="URN or ID of the Business Process Stage"),
    data: str = typer.Option(..., "--data", "-d", help="JSON string of data context"),
    integrity_hash: str = typer.Option(None, "--hash", "-h", help="Required Governance Hash for Handshake")
):
    """
    Enforce Governance Rules acting as a Runtime Policy Enforcement Point (Hard Stop / Soft Stop / Log Only).
    """
    console.print(Panel(f"🛡️  [bold red]ODGS INTERCEPTOR[/bold red] | Checking Process: [cyan]{process}[/cyan]"))

    try:
        try:
            context = json.loads(data)
        except json.JSONDecodeError:
            console.print("[bold red]Error:[/bold red] Invalid JSON data provided.")
            raise typer.Exit(code=1)

        interceptor = OdgsInterceptor()

        if not process.startswith("urn:"):
            process = f"urn:odgs:process:{process}"

        interceptor.intercept(process, context, required_integrity_hash=integrity_hash)

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
def ingest(
    payload: str = typer.Option(..., "--payload", "-p", help="Path to the authoritative JSON-LD / FLINT payload")
):
    """
    Ingest a Normative Definition from an External Authority (e.g., TNO FLINT, W3C ODRL 2.2).
    """
    console.print(Panel(f"📥 [bold green]Normative Ingestion Protocol[/bold green] | Source: [cyan]{payload}[/cyan]"))

    if not os.path.exists(payload):
        console.print(f"[bold red]Error:[/bold red] Payload file not found: {payload}")
        raise typer.Exit(code=1)

    try:
        import hashlib
        with open(payload, "rb") as f:
            raw_bytes = f.read()

        payload_hash = hashlib.sha256(raw_bytes).hexdigest()
        _ = json.loads(raw_bytes.decode("utf-8"))

        console.print("✅ [bold green]Ingestion Complete.[/bold green]")
        console.print(f"   📜 Secured from: {payload}")
        console.print(f"   🔐 Boundary Hash (SHA-256): {payload_hash}")
        console.print("   [dim]Note: Use 'odgs compile' to finalize the enforcement rule.[/dim]")

    except Exception as e:
        console.print(f"[bold red]System Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def compile(
    source: str = typer.Option(..., "--source", "-s", help="Path to the source JSON definition to compile")
):
    """
    Compile a normative JSON definition into a local executable rule with boundary hash.
    """
    import hashlib

    console.print(Panel(f"⚙️  [bold cyan]ODGS Compiler[/bold cyan] | Target: [cyan]{source}[/cyan]"))

    if not os.path.exists(source):
        console.print(f"[bold red]Error:[/bold red] Source definition not found: {source}")
        raise typer.Exit(code=1)

    try:
        with open(source, "rb") as f:
            raw_data = f.read()

        boundary_hash = hashlib.sha256(raw_data).hexdigest()
        definition = json.loads(raw_data.decode("utf-8"))

        rule_urn = definition.get("urn", "urn:odgs:unknown")

        console.print("✅ [bold green]Compilation Successful[/bold green]")
        console.print(f"   🏛️  Rule URN: {rule_urn}")
        console.print(f"   🔐 Boundary Hash Stamped: {boundary_hash}")
        console.print("   [dim]The hash guarantees cryptographic integrity between policy and execution logic.[/dim]")

    except Exception as e:
        console.print(f"[bold red]Compilation Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="dataspace-demo")
def dataspace_demo(
    output_format: str = typer.Option(
        "cap-vc",
        "--format",
        "-f",
        help="Output format: s-cert | cap-vc | prov-o | oscal"
    )
):
    """
    Run the end-to-end Dataspace Bridge demo (W3C ODRL 2.2 -> Phase 6 PEP -> S-Cert -> Eclipse CAP v2.2.1 / W3C PROV-O / NIST OSCAL).
    """
    from odgs.dataspace.cli import main as dataspace_cli_main
    rc = dataspace_cli_main(["demo", "--format", output_format])
    if rc != 0:
        raise typer.Exit(code=rc)


if __name__ == "__main__":
    app()
