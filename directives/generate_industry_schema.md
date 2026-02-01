# Directive: Generate High-Risk Industry Schema

**Goal**: Create a valid ODGS governance schema for a specific EU AI Act "High-Risk" industry.

## Inputs
- `industry_name`: The target sector (e.g., "Critical Infrastructure", "Biometrics").
- `output_dir`: Path to generate the schema files (default: `protocol/lib/<industry_slug>`).

## Tools
- `execution/generate_schema.py`: Generates the initial JSON drafts based on templates.
- `execution/validate_and_feedback.py`: Validates the generated JSON and returns specific errors.

## Instructions (The Annealing Loop)

1.  **Generate Draft**:
    Run `execution/generate_schema.py --industry "<industry_name>" --output "<output_dir>"`
    
    *This will create `standard_metrics.json` and `standard_data_rules.json` populated with industry-specific templates.*

2.  **Validate**:
    Run `execution/validate_and_feedback.py --path "<output_dir>"`

3.  **Anneal (If Error)**:
    If validation returns "status": "error":
    - Read the "issues" list from the output.
    - **ACTION**: You (the Agent) must read the JSON file, fix the specific syntax or schema violation (e.g., missing "owner" field, invalid "compliance" tag).
    - Save the corrected file.
    - Go back to Step 2 (Validate).

4.  **Finalize**:
    When validation returns "status": "success":
    - Commit the files to the repository.
    - Log the success.

## Edge Cases
- **Duplicate IDs**: If `metric_id` conflicts, append a random suffix (e.g., `_V2`).
- **Missing Directory**: Ensure `output_dir` exists before writing.
