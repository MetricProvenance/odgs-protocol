import os
import json
from google import genai
from google.genai import types

def generate_with_gemini(industry, api_key):
    """
    Uses Gemini 3.0 (latest) to research and generate a novel schema with Google Search.
    Two-step process to avoid API conflicts.
    """
    print(f"✨ Connecting to Gemini 3.0 for '{industry}'...")
    client = genai.Client(api_key=api_key)
    
    # STEP 1: Research with Google Search (no JSON mode)
    research_prompt = f"""
    You are an expert Data Governance Engineer specializing in the EU AI Act, CIRPASS 2, and TNO standards.
    
    **OBJECTIVE**: Conduct comprehensive research for the "{industry}" industry to support generation of a PRODUCTION-GRADE governance bundle.
    
    **RESEARCH REQUIREMENTS**:
    1. **Regulatory Landscape**: EU AI Act requirements, CIRPASS 2 mandates (if applicable), ISO standards, TNO Semantic Treehouse alignment
    2. **Industry KPIs**: Identify 25-35 critical metrics across domains:
       - Financial Performance (ROI, margins, cash flow)
       - Operational Efficiency (cycle time, throughput, utilization)
       - Quality Management (defect rates, compliance scores)
       - Sustainability (carbon footprint, energy intensity, waste reduction)
       - Safety & Compliance (incident rates, audit scores)
    3. **Data Quality Dimensions**: Which DQ dimensions (Accuracy, Completeness, Timeliness, etc.) are most critical for each metric?
    4. **Cross-Industry Benchmarks**: Compare with similar industries (e.g., Battery Passport vs Automotive, Green Steel vs Heavy Manufacturing)
    5. **Validation Rules**: Common data integrity checks, referential constraints, business rules
    
    **DEPTH REQUIREMENT**: Your research should support generation of AT LEAST 20 metrics and 15 rules. Provide specific examples, formulas, and industry standards.
    
    **OUTPUT**: Comprehensive research summary with citations and specific metric examples.
    """
    
    try:
        print("🔍 Step 1: Researching with Google Search...")
        google_search_tool = types.Tool(google_search=types.GoogleSearch())
        
        research_response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=research_prompt,
            config=types.GenerateContentConfig(tools=[google_search_tool])
        )
        
        research_findings = research_response.text
        print(f"✅ Research complete ({len(research_findings)} chars)")
        
        # STEP 2: Generate JSON based on research (no Search tool)
        print("📝 Step 2: Generating structured JSON bundle...")
        
        generation_prompt = f"""
        Based on this research for the "{industry}" industry:
        
        {research_findings}
        
        Generate a PRODUCTION-GRADE "Governance Bundle" as a JSON object with 4 keys: "metrics", "rules", "ontology", "physical_map".
        
        **MANDATORY OUTPUT REQUIREMENTS**:
        You MUST generate a minimum of **30 METRICS** and **20 RULES**. Do not summarize. Do not truncate.
        
        **SECTION 1: METRICS (Generate at least 30)**
        Distribute these metrics across the following domains (5-6 metrics PER DOMAIN):
        1. **Financial Performance**: (e.g., Margin, ROI, Cost of Goods Sold)
        2. **Operational Efficiency**: (e.g., Cycle Time, Throughput, Utilization)
        3. **Quality & Compliance**: (e.g., Defect Rate, First Pass Yield, Audit Score)
        4. **Supply Chain / Logistics**: (e.g., On-Time Delivery, Inventory Turns)
        5. **Sustainability (ESG)**: (e.g., Carbon Footprint, Waste Ratio)
        6. **Risk & Safety**: (e.g., Incident Rate, Hazard Frequency)

        **METRIC SCHEMA**:
        ```json
        {{
          "metric_id": "urn:odgs:metric:<unique_slug>",
          "name": "Standard Name",
          "domain": "Domain Name",
          "calculation_logic": {{
            "abstract": "Clear English definition of the formula",
            "sql_standard": "SELECT ...",
            "dax_pattern": "CALCULATE(...)"
          }},
          "owner": "Business Role",
          "targetIndustries": ["{industry}"],
          "icon": "bi-graph-up",  // Valid Bootstrap Icon
          "definition": "Official legal/business definition.",
          "interpretation": "How to read this metric (High is Good/Bad).",
          "example": "Real-world example value.",
          "criticalDqDimensionIds": [1, 4] // IDs from DAMA standard
        }}
        ```

        **SECTION 2: RULES (Generate at least 20)**
        Focus on "Judiciary Plane" rules that VALIDATE the metrics above.
        - **Integrity Rules**: "Foreign Key match between Trade & Counterparty"
        - **Value Rules**: "Price must be > 0"
        - **Compliance Rules**: "GDPR retention limit checks"
        
        **RULE SCHEMA - STRICT STANDARD**:
        ```json
        {{
            "rule_id": "urn:odgs:rule:<unique_id>",
            "name": "Standard Rule Name",
            "domain": "Domain Name",
            "calculation_logic": {{
                "abstract": "Description of the validation logic",
                "sql_standard": "SELECT * FROM ... WHERE ...",
                "dax_pattern": "FILTER(...)"
            }},
            "owner": "Data_Steward",
            "severity": "Critical"
        }}
        ```
        
        **SECTION 3: ONTOLOGY & MAPPING**
        - **ontology**: Graph edges linking Metric -> Rule (relationship: "VALIDATED_BY")
        - **physical_map**: Sample bindings to a Data Warehouse (Snowflake/BigQuery).
        
        Output ONLY valid JSON.
        """
        
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=generation_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        # Try multiple ways to extract the data
        if hasattr(response, 'parsed') and response.parsed:
            data = response.parsed
            print(f"✅ Parsed data type: {type(data)}")
        elif hasattr(response, 'text'):
            import json
            data = json.loads(response.text)
            print(f"✅ Extracted from text, type: {type(data)}")
        else:
            print(f"❌ Could not extract data from response: {dir(response)}")
            return None
        
        # QUALITY VALIDATION
        metric_count = len(data.get('metrics', []))
        rule_count = len(data.get('rules', []))
        
        print(f"📊 Generated {metric_count} metrics, {rule_count} rules")
        
        # If below threshold, attempt one retry with explicit expansion request
        if metric_count < 15:
            print(f"⚠️  Metric count ({metric_count}) below minimum (15). Attempting expansion...")
            
            expansion_prompt = f"""
            The previous generation only produced {metric_count} metrics for "{industry}".
            
            **CRITICAL**: You MUST generate AT LEAST 20 metrics to meet industry standards.
            
            Expand the following bundle to include additional metrics across these underrepresented domains:
            - Operational Efficiency (add 5-7 metrics)
            - Quality & Compliance (add 3-5 metrics)
            - Sustainability & ESG (add 2-4 metrics)
            
            Previous bundle:
            {json.dumps(data, indent=2)}
            
            Output the COMPLETE expanded bundle with ALL original metrics plus new ones. Maintain the same JSON structure.
            """
            
            retry_response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=expansion_prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            
            if hasattr(retry_response, 'parsed') and retry_response.parsed:
                data = retry_response.parsed
            elif hasattr(retry_response, 'text'):
                data = json.loads(retry_response.text)
            
            metric_count = len(data.get('metrics', []))
            print(f"📊 After expansion: {metric_count} metrics, {len(data.get('rules', []))} rules")
            
        print("✨ Gemini successfully researched and generated a full Protocol Bundle.")
        return data
        
    except Exception as e:
        print(f"❌ Gemini Generation Failed: {e}")
        print("🔄 Attempting direct generation without search...")
        try:
            # Fallback: direct generation without research
            fallback_prompt = f"""
            Generate a governance bundle for "{industry}" industry.
            Output JSON with keys: "metrics", "rules", "ontology", "physical_map".
            Use URN format: "urn:odgs:metric:<id>" and "urn:odgs:rule:<id>".
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=fallback_prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return response.parsed
        except Exception as fallback_error:
            print(f"❌ Fallback also failed: {fallback_error}")
            return None

def write_bundle(data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
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

def run_agent_chat(prompt, context_files, api_key):
    """
    Runs a contextual chat session using the LLM with search tools enabled.
    """
    client = genai.Client(api_key=api_key)
    
    # Enable Google Search for real-time research
    google_search_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    context_data = {}
    for f_path in context_files:
        if os.path.exists(f_path):
            try:
                with open(f_path, 'r') as f:
                    context_data[os.path.basename(f_path)] = f.read()
            except:
                continue

    system_instruction = """
    You are the ODGS Governance Agent, an elite architect of "Semantic Integrity".
    
    CORE CONCEPT (SEMANTIC INTEGRITY):
    Semantic Integrity is achieved by following this chain:
    [Business Lifecycle] -> [Metrics] -> [Referential Integrity Rules] -> [DQ Dimensions]
    
    CAPABILITIES & CONTEXT:
    1. BUSINESS LIFECYCLE: Found in `business_process_maps.json`. This is the starting point.
    2. METRICS & RULES: Found in industry-specific files (e.g., `standard_metrics.json`).
    3. DQ DIMENSIONS: Found in `standard_dq_dimensions.json`. These map to Metrics/Rules.
    4. RESEARCH: You HAVE the 'google_search' tool. Use it for cross-industry research (Banking, HIPAA, etc.).
    
    INSTRUCTIONS:
    - When a user asks about a metric, link it to a Lifecycle Stage and a DQ Dimension.
    - If the user asks about a DQ Dimension like "Data Integrity", look it up in `standard_dq_dimensions.json`.
    - If you are researching other industries, use Google Search and then suggest how they would fit into this Semantic Integrity chain.
    - provide clickable [Links](URL) for research findings.
    """

    full_message = f"""
    {system_instruction}
    
    ---
    AVAILABLE GOVERNANCE FILES (CONTEXT):
    {json.dumps(context_data, indent=2)}
    ---
    
    USER QUERY:
    {prompt}
    """
    
    try:
        # Using gemini-2.5-flash which has excellent tool use performance
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_message,
            config=types.GenerateContentConfig(
                tools=[google_search_tool]
            )
        )
        return response.text
    except Exception as e:
        return f"Error connecting to agent: {str(e)}"
