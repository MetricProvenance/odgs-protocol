import json
import re
import os

# Paths relative to project root
DIMENSIONS_PATH = "../1_NORMATIVE_SPECIFICATION/schemas/legislative/standard_dq_dimensions.json"
RULES_PATH = "../1_NORMATIVE_SPECIFICATION/schemas/judiciary/standard_data_rules.json"
FACTORS_PATH = "../1_NORMATIVE_SPECIFICATION/schemas/judiciary/root_cause_factors.json"

def to_kebab_case(name):
    # Remove special chars and swap spaces for dashes
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    return re.sub(r'\s+', '-', name).lower()

def migrate():
    print(f"Loading Dimensions from {DIMENSIONS_PATH}...")
    try:
        with open(DIMENSIONS_PATH, 'r') as f:
            dimensions = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {DIMENSIONS_PATH}")
        return

    id_to_urn = {}
    dama_id_to_urn = {}
    
    print("Building URN Map...")
    for dim in dimensions:
        urn = f"urn:odgs:dimension:{to_kebab_case(dim['name'])}"
        id_to_urn[dim['id']] = urn
        if 'damaId' in dim:
            dama_id_to_urn[dim['damaId']] = urn
            
        # Optional: Add sovereign_urn to dimension if missing?
        # if 'sovereign_urn' not in dim:
        #    dim['sovereign_urn'] = None
    
    # Save dimensions back if we modified them? 
    # Not mostly needed for this specific migration step (ID -> URN refactor).

    print("Migrating Rules...")
    try:
        with open(RULES_PATH, 'r') as f:
            rules = json.load(f)
        
        for rule in rules:
            # 1. Transform ID to URN
            if 'rule_id' in rule:
                rule['urn'] = f"urn:odgs:rule:{rule['rule_id']}"
                del rule['rule_id']
            
            # 2. Transform Dimension Links
            if 'improvesDqDimensionIds' in rule:
                new_urns = []
                for pid in rule['improvesDqDimensionIds']:
                    if pid in id_to_urn:
                        new_urns.append(id_to_urn[pid])
                    else:
                        print(f"Warning: Rule {rule.get('name')} refers to unknown Dimension ID {pid}")
                
                rule['related_dimension_urns'] = new_urns
                del rule['improvesDqDimensionIds']

        with open(RULES_PATH, 'w') as f:
            json.dump(rules, f, indent=2)
        print(f"Updated {RULES_PATH}")
            
    except FileNotFoundError:
        print(f"Skipping Rules (File not found: {RULES_PATH})")

    print("Migrating Factors...")
    try:
        with open(FACTORS_PATH, 'r') as f:
            factors = json.load(f)
            
        for factor in factors:
            if 'dqDimensionsImpactedDamaIds' in factor:
                new_urns = []
                for did in factor['dqDimensionsImpactedDamaIds']:
                    if did in dama_id_to_urn:
                        new_urns.append(dama_id_to_urn[did])
                    else:
                        print(f"Warning: Factor {factor.get('factorName')} refers to unknown DAMA ID {did}")
                
                factor['related_dimension_urns'] = new_urns
                del factor['dqDimensionsImpactedDamaIds']
                
        with open(FACTORS_PATH, 'w') as f:
            json.dump(factors, f, indent=2)
        print(f"Updated {FACTORS_PATH}")

    except FileNotFoundError:
        print(f"Skipping Factors (File not found: {FACTORS_PATH})")

if __name__ == "__main__":
    migrate()
