import argparse
import json
import os
import sys
import google.generativeai as genai

# Knowledge Base: Templates for High-Risk Industries
# Aligned with EU AI Act Annex III
TEMPLATES = {
    "Critical Infrastructure": {
        "metrics": [
            {
                "metric_id": "KPI_CI_001",
                "name": "Grid_Uptime_Percentage",
                "domain": "Operations",
                "definition": "Percentage of time the energy grid is operational without interruption.",
                "calculation_logic": {
                    "abstract": "(Total Hours - Downtime) / Total Hours",
                    "sql_standard": "AVG(CASE WHEN status = 'active' THEN 1 ELSE 0 END)"
                },
                "owner": "Ops_Director",
                "status": "Active",
                "compliance": {
                    "ai_risk_level": "High",
                    "gdpr_pii": False,
                    "data_classification": "Critical"
                }
            }
        ],
        "rules": [
             {
                "rule_id": "RULE_CI_001",
                "name": "Voltage_Range_Check",
                "domain": "Safety",
                "calculation_logic": {
                    "abstract": "Voltage must be between 220V and 240V",
                     "sql_standard": "voltage BETWEEN 220 AND 240"
                },
                "owner": "Safety_Team"
            }
        ]
    },
    "Biometrics": {
        "metrics": [
             {
                "metric_id": "KPI_BIO_001",
                "name": "False_Acceptance_Rate",
                "domain": "Security",
                "definition": "Rate at which unauthorized persons are incorrectly accepted.",
                "calculation_logic": {
                    "abstract": "False Accepts / Total Attempts",
                    "sql_standard": "SUM(false_accepts) / COUNT(*)"
                },
                "owner": "CISO",
                "status": "Active",
                 "compliance": {
                    "ai_risk_level": "Unacceptable Risk", 
                    "gdpr_pii": True,
                    "data_classification": "Restricted"
                }
            }
        ],
        "rules": []
    },
    "Education": {
        "metrics": [
            {
                "metric_id": "KPI_EDU_001",
                "name": "Student_Assignment_Score",
                "domain": "Education",
                "definition": "Automated scoring of student assignments.",
                "calculation_logic": {
                    "abstract": "Sum of points / Max points",
                    "sql_standard": "SUM(points_awarded) / SUM(max_points)"
                },
                "owner": "Academic_Board",
                "status": "Active",
                 "compliance": {
                    "ai_risk_level": "High", 
                    "gdpr_pii": True,
                    "data_classification": "Confidential"
                }
            }
        ],
        "rules": []
    },
    "Employment": {
        "metrics": [
            {
                "metric_id": "KPI_HR_001",
                "name": "Candidate_Screening_Score",
                "domain": "HR",
                "definition": "Automated ranking of job applicants.",
                "calculation_logic": {
                    "abstract": "Weighted sum of skills matches",
                    "sql_standard": "SUM(skill_weight * match_score)"
                },
                "owner": "HR_Director",
                "status": "Active",
                 "compliance": {
                    "ai_risk_level": "High", 
                    "gdpr_pii": True,
                    "data_classification": "Confidential"
                }
            }
        ],
        "rules": []
    },
    "Essential Services": {
        "metrics": [
            {
                "metric_id": "KPI_CREDIT_001",
                "name": "Creditworthiness_Score",
                "domain": "Finance",
                "definition": "Score determining eligibility for essential public services or benefits.",
                "calculation_logic": {
                    "abstract": "Risk Model Output",
                    "sql_standard": "prediction_score"
                },
                "owner": "Risk_Officer",
                "status": "Active",
                 "compliance": {
                    "ai_risk_level": "High", 
                    "gdpr_pii": True,
                    "data_classification": "Confidential"
                }
            }
        ],
        "rules": []
    },
    "Law Enforcement": {
        "metrics": [
            {
                "metric_id": "KPI_LE_001",
                "name": "Recidivism_Risk_Score",
                "domain": "Justice",
                "definition": "Predicted risk of re-offending.",
                "calculation_logic": {
                    "abstract": "Model Inference",
                    "sql_standard": "inference_output"
                },
                "owner": "Department_Justice",
                "status": "Active",
                 "compliance": {
                    "ai_risk_level": "High", 
                    "gdpr_pii": True,
                    "data_classification": "Restricted"
                }
            }
        ],
        "rules": []
    },
    "Migration": {
        "metrics": [
            {
                "metric_id": "KPI_MIG_001",
                "name": "Asylum_Eligibility_Score",
                "domain": "Immigration",
                "definition": "Automated assessment of asylum claims.",
                "calculation_logic": {
                    "abstract": "Claim Validity Score",
                    "sql_standard": "validity_index"
                },
                "owner": "Immigration_Office",
                "status": "Active",
                 "compliance": {
                    "ai_risk_level": "High", 
                    "gdpr_pii": True,
                    "data_classification": "Restricted"
                }
            }
        ],
        "rules": []
    },
    "Justice": {
        "metrics": [
            {
                "metric_id": "KPI_JUS_001",
                "name": "Judicial_Outcome_Prediction",
                "domain": "Legal",
                "definition": "Prediction of court sentence or ruling.",
                "calculation_logic": {
                    "abstract": "Case Precedent Match",
                    "sql_standard": "match_probability"
                },
                "owner": "Court_Admin",
                "status": "Active",
                 "compliance": {
                    "ai_risk_level": "High", 
                    "gdpr_pii": True,
                    "data_classification": "Restricted"
                }
            }
        ],
        "rules": []
    }
}

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_with_gemini(industry, api_key):
    """
    Uses Gemini 3.0 Flash to generate a novel schema for the industry.
    """
    print(f"✨ Connecting to Gemini for '{industry}'...")
    genai.configure(api_key=api_key)
    
    # Try Flash first, then Pro
    try:
        model = genai.GenerativeModel('gemini-3-flash-preview') 
    except:
        model = genai.GenerativeModel('gemini-3-pro-preview')
    
    prompt = """
    You are an expert Data Governance Engineer specializing in the EU AI Act and ODGS (Open Data Governance Standard).
    Generate a full "Governance Bundle" for the "{industry}" industry.
    
    Output a JSON object with 4 keys: "metrics", "rules", "ontology", "physical_map".
    
    CONSTRAINTS:
    1. Use URN stability: Metrics must have URNs like "urn:odgs:metric:<id>". Rules must have "urn:odgs:rule:<id>".
    2. The "ontology" must link these URNs using the "VALIDATED_BY" relationship.
    3. The "physical_map" must map these URNs to hypothetical warehouse tables (Snowflake/Databricks).
    
    Structure:
    - metrics: List of objects with [metric_id, name, domain, definition, calculation_logic (as an object with "abstract" and "sql_standard" keys), owner, compliance (ai_risk_level, gdpr_pii, data_classification)]
    - rules: List of objects with [rule_id, name, domain, calculation_logic (as an object with "abstract" and "sql_standard" keys), owner]
    - ontology: Object with [meta, graph_edges (source_urn, target_urn, relationship="VALIDATED_BY")]
    - physical_map: Object with [meta, mappings (concept_urn, concept_name, bindings (platform, database, schema, table, column_mapping))]
    
    CRITICAL: "calculation_logic" MUST be a JSON object, e.g., {"abstract": "...", "sql_standard": "..."}.
    
    Output ONLY valid JSON. No markdown fencing.
    """.replace("{industry}", industry)
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        print("✨ Gemini successfully dreamed up a full Protocol Bundle.")
        return data
    except Exception as e:
        print(f"❌ Gemini Generation Failed: {e}")
        return None

def generate_schema(industry, output_dir):
    print(f"🏭 Accessing Schema Forge for: {industry}")
    
    # Try Gemini first if API Key exists
    api_key = os.getenv("GEMINI_API_KEY")
    data = None
    
    if api_key:
        data = generate_with_gemini(industry, api_key)
        
    # Fallback to templates
    if not data:
        print(f"ℹ️  Using Standard Template for '{industry}'")
        data = TEMPLATES.get(industry)
        
    if not data:
        print(f"⚠️  No template found for '{industry}'. Generically seeding...")
        data = {
            "metrics": [{
                "metric_id": "KPI_GEN_001",
                "name": "Generic_Metric", 
                "domain": industry,
                "definition": "Placeholder metric",
                "calculation_logic": {"abstract": "N/A", "sql_standard": "NULL"},
                "owner": "Admin"
            }],
            "rules": [],
            "ontology": {"meta": {}, "graph_edges": []},
            "physical_map": {"meta": {}, "mappings": []}
        }

    os.makedirs(output_dir, exist_ok=True)
    
    # Write 4-file bundle
    files_to_write = {
        "standard_metrics.json": data.get("metrics", []),
        "standard_data_rules.json": data.get("rules", []),
        "ontology_graph.json": data.get("ontology", {"meta": {}, "graph_edges": []}),
        "physical_data_map.json": data.get("physical_map", {"meta": {}, "mappings": []})
    }

    for filename, content in files_to_write.items():
        path = os.path.join(output_dir, filename)
        with open(path, 'w') as f:
            json.dump(content, f, indent=2)
        print(f"✅ Generated {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--industry", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    generate_schema(args.industry, args.output)
