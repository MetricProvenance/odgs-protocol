import sys
import os
import logging

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from odgs.executive.interceptor import OdgsInterceptor, ProcessBlockedException

def run_test():
    print("🚗 Starting ODGS Drive Test...")
    
    interceptor = OdgsInterceptor()
    
    # Scene 1: NHG Issuance (Context Aware)
    # Context ID: "NHG_ISSUANCE" validates against rule 2004 (Email) and 2027 (Date)
    
    print("\n--- TEST 1: NHG Issuance (Valid Data) ---")
    valid_data = {
        "email": "citizen@example.com",
        "transaction_date": "2024-01-01",
        "value": "2024-01-01" # For Rule 2027
    }
    
    try:
        interceptor.intercept("NHG_ISSUANCE", valid_data, "hash_123")
        print("✅ SUCCESS: Valid data passed.")
    except ProcessBlockedException as e:
        print(f"❌ FAILURE: Unexpected Block: {e}")

    print("\n--- TEST 2: NHG Issuance (Invalid Email) ---")
    invalid_email_data = {
        "email": "invalid-email",
        "transaction_date": "2024-01-01",
        "value": "2024-01-01"
    }
    
    try:
        interceptor.intercept("NHG_ISSUANCE", invalid_email_data, "hash_123")
        print("❌ FAILURE: Invalid email should have been blocked.")
    except ProcessBlockedException as e:
        print(f"✅ SUCCESS: Blocked as expected: {e}")

    print("\n--- TEST 3: Parking Audit (Regex check for Container?? No, Rule 2021 is Shipping Package) ---")
    # Rule 2021: ^[A-Z]{4}[0-9]{7}$
    
    print("--- TEST 3: Shipping Container Check (Rule 2021) ---")
    container_data = {
        "value": "MSKU1234567"
    }
    try:
        interceptor.intercept("PARKING_AUDIT", container_data, "hash_123")
        print("✅ SUCCESS: Valid Container ID passed.")
    except ProcessBlockedException as e:
         print(f"❌ FAILURE: Unexpected Block: {e}")

    container_data_bad = {
        "value": "BAD-ID"
    }
    try:
        interceptor.intercept("PARKING_AUDIT", container_data_bad, "hash_123")
        print("❌ FAILURE: Invalid Container ID should have been blocked.")
    except ProcessBlockedException as e:
         print(f"✅ SUCCESS: Blocked as expected: {e}")

if __name__ == "__main__":
    run_test()
