# Directive: Generate Novel Industry Schema

**Goal**: Create a valid ODGS governance schema for a **Novel** or **Custom** industry using Gemini 3.0.

## Inputs
- `industry_name`: The target sector (e.g., "Space Exploration", "Quantum Computing").
- `output_dir`: Path to generate the schema files.

## Tools
- `execution/generate_schema.py`: Detects `GEMINI_API_KEY` and prompts the LLM for definitions.
- `execution/validate_and_feedback.py`: Validation loop.

## Instructions

1.  **Ensure Environment**:
    Check that `.env` contains `GEMINI_API_KEY`.

2.  **Generate Draft**:
    Run `execution/generate_schema.py --industry "<industry_name>" --output "<output_dir>"`
    *(The script will print "Connecting to Gemini 3.0 Flash..." if successful)*

3.  **Validate & Anneal**:
    Run the standard validation loop:
    `execution/validate_and_feedback.py --path "<output_dir>"`
    
    *If Gemini makes a structural error (it's probabilistic!), the validation script catching it allows you (the Orchestrator) to re-prompt or manually fix.*
