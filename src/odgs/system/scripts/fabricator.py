
import random
import string
import json

def generate_container_id(valid=True):
    if valid:
        # Standard ISO 6346: 4 letters, 7 numbers
        owner_code = "".join(random.choices(string.ascii_uppercase, k=4))
        serial_number = "".join(random.choices(string.digits, k=7))
        return f"{owner_code}{serial_number}"
    else:
        # Invalid format
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

def fabricate_data_context(scenario="valid"):
    """
    Generates a data context for the Sovereign Interceptor.
    Scenarios: 'valid', 'invalid_format', 'missing_field'
    """
    
    data = {
        "shipment_id": f"SHP_{random.randint(1000, 9999)}",
        "origin_port": random.choice(["NLRTM", "CNSHG", "USNYC", "SGSIN"]),
        "destination_port": random.choice(["DEHAM", "BEANR", "JPTYO", "AUMEL"]),
        "container_id": generate_container_id(valid=(scenario == "valid"))
    }
    
    if scenario == "missing_field":
        del data["container_id"]
        
    return data

if __name__ == "__main__":
    print(json.dumps(fabricate_data_context("valid"), indent=2))
