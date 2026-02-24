import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from odgs.system.config import settings

# --- CONSTANTS ---
URN_PREFIX_METRIC = "urn:odgs:metric:"
URN_PREFIX_RULE = "urn:odgs:rule:"
URN_PREFIX_DEF = "urn:odgs:def:"
URN_PREFIX_DIM = "urn:odgs:dimension:"
URN_PREFIX_PROCESS = "urn:odgs:process:"
URN_PREFIX_FACTOR = "urn:odgs:factor:"

class GovernanceGraph:
    """
    In-memory graph engine for resolving Sovereign Lineage.
    Loads all 5 planes: Legislative, Judiciary, Executive, Sovereign, Physical.
    """
    def __init__(self):
        self.metrics = {}       # id -> dict
        self.rules = {}         # id -> dict
        self.definitions = {}   # urn -> dict
        self.edges = []         # list of dicts
        self.dq_dimensions = {} # id -> dict
        self.context_bindings = []  # list of context dicts
        self.physical_maps = []     # list of mapping dicts
        self.business_processes = [] # list of lifecycle dicts
        self.root_cause_factors = [] # list of factor dicts
        self._load_data()

    def _load_data(self):
        """Load all JSON artifacts into memory."""
        root = settings.PROJECT_ROOT

        # ─── 1. LEGISLATIVE PLANE ───
        leg_path = root / "1_NORMATIVE_SPECIFICATION" / "schemas" / "legislative"
        if leg_path.exists():
            # Metrics
            try:
                m_data = json.loads((leg_path / "standard_metrics.json").read_text())
                for m in m_data:
                    self.metrics[m["metric_id"]] = m
            except (json.JSONDecodeError, KeyError, OSError): pass

            # DQ Dimensions
            try:
                dq_data = json.loads((leg_path / "standard_dq_dimensions.json").read_text())
                for d in dq_data:
                    self.dq_dimensions[d["id"]] = d
            except (json.JSONDecodeError, KeyError, OSError): pass

            # Graph
            try:
                g_data = json.loads((leg_path / "ontology_graph.json").read_text())
                self.edges = g_data.get("graph_edges", [])
            except (json.JSONDecodeError, KeyError, OSError): pass

        # ─── 2. JUDICIARY PLANE ───
        jud_path = root / "1_NORMATIVE_SPECIFICATION" / "schemas" / "judiciary"
        if (jud_path / "standard_data_rules.json").exists():
            try:
                r_data = json.loads((jud_path / "standard_data_rules.json").read_text())
                for r in r_data:
                    rule_id = r.get("rule_id")
                    if rule_id:
                        self.rules[str(rule_id)] = r
                        self.rules[f"{URN_PREFIX_RULE}{rule_id}"] = r
            except Exception as e:
                print(f"Error loading Rules: {e}")

        # Root Cause Factors
        if (jud_path / "root_cause_factors.json").exists():
            try:
                self.root_cause_factors = json.loads(
                    (jud_path / "root_cause_factors.json").read_text()
                )
            except (json.JSONDecodeError, OSError): pass

        # ─── 3. EXECUTIVE PLANE ───
        exec_path = root / "1_NORMATIVE_SPECIFICATION" / "schemas" / "executive"
        if exec_path.exists():
            # Context Bindings
            try:
                cb_data = json.loads((exec_path / "context_bindings.json").read_text())
                self.context_bindings = cb_data.get("contexts", [])
            except (json.JSONDecodeError, KeyError, OSError): pass

            # Physical Data Map
            try:
                pm_data = json.loads((exec_path / "physical_data_map.json").read_text())
                self.physical_maps = pm_data.get("mappings", [])
            except (json.JSONDecodeError, KeyError, OSError): pass

            # Business Process Maps
            try:
                self.business_processes = json.loads(
                    (exec_path / "business_process_maps.json").read_text()
                )
            except (json.JSONDecodeError, OSError): pass

        # ─── 4. SOVEREIGN PLANE ───
        paths = [
            root / "1_NORMATIVE_SPECIFICATION" / "schemas" / "sovereign",
            settings.DRAFTS_DIR
        ]
        for p in paths:
            if p.exists():
                for f in p.rglob("*.json"):
                    if "01-definitions-schema.json" in f.name: continue
                    try:
                        data = json.loads(f.read_text())
                        if "urn" not in data:
                            continue
                        def_urn = data["urn"]
                        self.definitions[def_urn] = data
                        for rel in data.get("relations", []):
                            rel_type = rel.get("type", "")
                            target = rel.get("target_urn", "")
                            if not target: continue
                            rel_map = {
                                "isDefinedBy":  "IS_DEFINED_BY",
                                "IS_DEFINED_BY": "IS_DEFINED_BY",
                                "VALIDATED_BY": "VALIDATED_BY",
                                "validatedBy":  "VALIDATED_BY",
                                "DEFINES":      "IS_DEFINED_BY",
                            }
                            canonical = rel_map.get(rel_type, rel_type.upper())
                            self.edges.append({
                                "link_id":      f"AUTO_{def_urn}",
                                "source_urn":   target,
                                "target_urn":   def_urn,
                                "relationship": canonical,
                                "weight":       1.0,
                                "description":  f"Auto-ingested from {f.name}",
                            })
                    except Exception as e:
                        print(f"Error loading definition {f}: {e}")

        self._auto_link_dimensions()

    def _auto_link_dimensions(self):
        """Automatically add edges from metrics and rules to dimensions if not present."""
        for mid, metric in self.metrics.items():
            if not mid.startswith(URN_PREFIX_METRIC): continue
            for dim_id in metric.get("criticalDqDimensionIds", []):
                t_urn = f"{URN_PREFIX_DIM}{dim_id}"
                l_id = f"AUTO_M_{mid.split(':')[-1]}_D_{dim_id}"
                self.edges.append({"link_id": l_id, "source_urn": mid, "target_urn": t_urn, "relationship": "CRITICAL_FOR", "weight": 1.0, "description": "Auto-linked Critical DQ Dimension"})
                
        for rid, rule in self.rules.items():
            if not rid.startswith(URN_PREFIX_RULE): continue
            for dim_id in rule.get("improvesDqDimensionIds", []):
                t_urn = f"{URN_PREFIX_DIM}{dim_id}"
                l_id = f"AUTO_R_{rid.split(':')[-1]}_D_{dim_id}"
                self.edges.append({"link_id": l_id, "source_urn": rid, "target_urn": t_urn, "relationship": "IMPROVES_DIMENSION", "weight": 1.0, "description": "Auto-linked Improves DQ Dimension"})

    # ─── COMPLIANCE MATRIX ───
    def get_compliance_matrix(self) -> pd.DataFrame:
        """Build the Status Table for all metrics."""
        rows = []
        for mid, m in self.metrics.items():
            metric_urn = f"{URN_PREFIX_METRIC}{mid}"

            linked_def = None
            authority = "None"
            status = "Naked"

            for edge in self.edges:
                if edge.get("source_urn") == metric_urn and edge.get("relationship") == "IS_DEFINED_BY":
                    target = edge.get("target_urn")
                    if target in self.definitions:
                        linked_def = self.definitions[target]
                        break
                if edge.get("target_urn") == metric_urn and edge.get("relationship") == "DEFINES_METRIC":
                     source = edge.get("source_urn")
                     if source in self.definitions:
                         linked_def = self.definitions[source]
                         break

            if linked_def:
                authority = linked_def.get("metadata", {}).get("authority_id", "Unknown")
                if authority == "AI_SYNTHETIC":
                    status = "Draft (AI)"
                else:
                    status = "Sovereign"

            # Resolve linked DQ dimensions
            dq_ids = m.get("criticalDqDimensionIds", [])
            dq_names = [self.dq_dimensions.get(did, {}).get("name", f"DQ-{did}") for did in dq_ids]

            # Count linked rules
            linked_rules = sum(
                1 for e in self.edges
                if e.get("source_urn") == metric_urn and e.get("relationship") == "VALIDATED_BY"
            )

            rows.append({
                "ID": mid,
                "Metric Name": m.get("name"),
                "Domain": m.get("domain", "General"),
                "Authority": authority,
                "Status": status,
                "DQ Dims": len(dq_ids),
                "Rules": linked_rules,
                "_urn": metric_urn,
                "_dq_names": ", ".join(dq_names) if dq_names else "—",
                "_icon": m.get("icon", ""),
                "_calc_abstract": (m.get("calculation_logic") or {}).get("abstract", "—"),
                "_calc_sql": (m.get("calculation_logic") or {}).get("sql_standard", "—"),
                "_calc_dax": (m.get("calculation_logic") or {}).get("dax_pattern", "—"),
                "_definition": m.get("definition", ""),
                "_interpretation": m.get("interpretation", ""),
                "_example": m.get("example", ""),
                "_industries": ", ".join(m.get("targetIndustries", [])),
            })

        return pd.DataFrame(rows)

    # ─── METRIC LINEAGE ───
    def get_metric_lineage(self, metric_id: str) -> Optional[Dict[str, Any]]:
        """Resolve the Semantic Triplet: Business + Logic + Law."""
        if metric_id not in self.metrics:
            return None

        metric = self.metrics[metric_id]
        metric_urn = f"{URN_PREFIX_METRIC}{metric_id}"

        # Resolve Rules (VALIDATED_BY)
        enforcing_rules = []
        for edge in self.edges:
            if edge.get("source_urn") == metric_urn and edge.get("relationship") == "VALIDATED_BY":
                rule_urn = edge.get("target_urn", "")
                rule_id = rule_urn.replace(URN_PREFIX_RULE, "")
                if rule_id in self.rules:
                    enforcing_rules.append(self.rules[rule_id])

        # Resolve Law (IS_DEFINED_BY)
        sovereign_def = None
        for edge in self.edges:
            if edge.get("source_urn") == metric_urn and edge.get("relationship") == "IS_DEFINED_BY":
                 target = edge.get("target_urn")
                 if target in self.definitions:
                     sovereign_def = self.definitions[target]
                     break

        # Fuzzy Match for AI Drafts
        if not sovereign_def:
            target_name = metric.get("name", "").lower().replace(" ", "_")
            for urn, d in self.definitions.items():
                if target_name in urn:
                    sovereign_def = d
                    break

        # Resolve Physical Binding
        physical_binding = None
        for pm in self.physical_maps:
            if pm.get("concept_urn") == metric_urn:
                physical_binding = pm
                break

        # Resolve DQ Dimensions
        dq_ids = metric.get("criticalDqDimensionIds", [])
        linked_dims = [self.dq_dimensions[did] for did in dq_ids if did in self.dq_dimensions]

        return {
            "metric": metric,
            "rules": enforcing_rules,
            "definition": sovereign_def,
            "physical": physical_binding,
            "dq_dimensions": linked_dims,
        }

    # ─── DQ DIMENSIONS ───
    def get_dq_dimensions_df(self) -> pd.DataFrame:
        """Return all DQ dimensions as a DataFrame."""
        rows = []
        for did, d in self.dq_dimensions.items():
            # Count linked metrics
            linked_metrics = sum(
                1 for m in self.metrics.values()
                if did in m.get("criticalDqDimensionIds", [])
            )
            # Count linked rules
            linked_rules = sum(
                1 for r_id, r in self.rules.items()
                if not r_id.startswith("urn:") and did in r.get("improvesDqDimensionIds", [])
            )
            rows.append({
                "ID": did,
                "Name": d.get("name", ""),
                "Category": d.get("category", ""),
                "Definition": d.get("definition", ""),
                "Unit": d.get("unitOfMeasure", ""),
                "Icon": d.get("icon", ""),
                "Linked Metrics": linked_metrics,
                "Linked Rules": linked_rules,
            })
        return pd.DataFrame(rows)

    def get_dq_dimension_detail(self, dim_id: int) -> Optional[Dict[str, Any]]:
        """Get full detail for a single DQ dimension."""
        return self.dq_dimensions.get(dim_id)

    # ─── CONTEXT BINDINGS ───
    def get_context_for_process(self, process_urn: str) -> Optional[Dict[str, Any]]:
        """Find context binding for a process URN."""
        for ctx in self.context_bindings:
            if ctx.get("context_id") == process_urn:
                return ctx
        return None

    def get_all_contexts(self) -> List[Dict[str, Any]]:
        """Return all context bindings."""
        return self.context_bindings

    # ─── PHYSICAL MAP ───
    def get_physical_binding(self, metric_urn: str) -> Optional[Dict[str, Any]]:
        """Find physical data map for a metric."""
        for pm in self.physical_maps:
            if pm.get("concept_urn") == metric_urn:
                return pm
        return None

    # ─── BUSINESS PROCESSES ───
    def get_business_processes(self) -> List[Dict[str, Any]]:
        """Return all business process lifecycles."""
        return self.business_processes

    # ─── DRAFT BUNDLES ───
    def get_draft_bundles(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group AI-generated definitions by bundle/industry."""
        bundles = {}
        drafts_dir = settings.DRAFTS_DIR
        if not drafts_dir.exists():
            return bundles
        for industry_dir in drafts_dir.iterdir():
            if industry_dir.is_dir():
                defs = []
                for f in industry_dir.glob("*.json"):
                    try:
                        defs.append(json.loads(f.read_text()))
                    except (json.JSONDecodeError, OSError):
                        pass
                if defs:
                    bundles[industry_dir.name] = defs
        return bundles

    # ─── PHASE STATS ───
    def get_phase_stats(self) -> Dict[str, Any]:
        """Return feature coverage statistics for the UI dashboard."""
        seen_ids = set()
        unique_rules_list = []
        for rid, r in self.rules.items():
            canon = str(r.get("rule_id", rid))
            if canon not in seen_ids:
                seen_ids.add(canon)
                unique_rules_list.append(r)

        rules_with_logic = sum(1 for r in unique_rules_list if r.get("logic_expression"))
        rules_with_severity = sum(1 for r in unique_rules_list if r.get("severity"))
        metrics_with_urn = sum(1 for m in self.metrics.values() if m.get("urn"))
        rules_with_urn = sum(1 for r in unique_rules_list if r.get("urn"))

        return {
            "rules_with_logic": rules_with_logic,
            "rules_with_severity": rules_with_severity,
            "metrics_with_urn": metrics_with_urn,
            "rules_with_urn": rules_with_urn,
            "context_bindings": len(self.context_bindings),
            "unique_rules": len(unique_rules_list),
            "total_metrics": len(self.metrics),
            "total_dq_dimensions": len(self.dq_dimensions),
            "total_physical_maps": len(self.physical_maps),
            "total_business_processes": len(self.business_processes),
            "total_definitions": len(self.definitions),
            "total_draft_bundles": sum(
                1 for d in self.definitions.values()
                if d.get("metadata", {}).get("authority_id") == "AI_SYNTHETIC"
            ),
        }


# Singleton
graph_engine = GovernanceGraph()
