#!/usr/bin/env python3
"""
Initialize the deployed contract via RPC calls
"""

import json
import requests
import base64
from neo3.wallet import Wallet
from neo3.core import types, cryptography
from neo3.contracts import CallFlags
from neo3 import vm

# Configuration
RPC_ENDPOINT = "http://seed1t5.neo.org:20332"
CONTRACT_HASH = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc"
MASTER_ACCOUNT = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"
TEE_ACCOUNT = "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"
MASTER_WIF = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb"

def address_to_script_hash(address):
    """Convert Neo address to script hash"""
    try:
        from neo3.wallet import utils
        script_hash = utils.address_to_script_hash(address)
        return f"0x{script_hash}"
    except:
        # Fallback method
        import base58
        decoded = base58.b58decode(address)
        return f"0x{decoded[1:21].hex()}"

def invoke_contract_test(method, params):
    """Test invoke a contract method"""
    payload = {
        "jsonrpc": "2.0",
        "method": "invokefunction",
        "params": [
            CONTRACT_HASH,
            method,
            params
        ],
        "id": 1
    }
    
    response = requests.post(RPC_ENDPOINT, json=payload)
    return response.json()

def check_contract_state():
    """Check if contract is already initialized"""
    print("🔍 Checking contract state...")
    
    # Check if initialized
    result = invoke_contract_test("isInitialized", [])
    if result.get("result", {}).get("stack", []):
        stack = result["result"]["stack"]
        if stack and stack[0].get("value") == "1":
            print("✅ Contract is already initialized")
            return True
    
    print("📝 Contract needs initialization")
    return False

def initialize_contract():
    """Initialize the contract"""
    print("\n🚀 Initializing contract...")
    
    # Convert addresses to script hashes
    master_hash = address_to_script_hash(MASTER_ACCOUNT)
    tee_hash = address_to_script_hash(TEE_ACCOUNT)
    
    params = [
        {"type": "Hash160", "value": master_hash},
        {"type": "Hash160", "value": tee_hash}
    ]
    
    result = invoke_contract_test("initialize", params)
    
    if result.get("result", {}).get("state") == "HALT":
        print("✅ Initialize test invocation successful")
        print(f"   Gas consumed: {result['result'].get('gasconsumed', 'N/A')}")
        return True
    else:
        print("❌ Initialize test invocation failed")
        print(f"   Error: {result.get('result', {}).get('exception', 'Unknown error')}")
        return False

def add_oracle():
    """Add TEE account as oracle"""
    print("\n🔧 Adding TEE account as oracle...")
    
    tee_hash = address_to_script_hash(TEE_ACCOUNT)
    params = [{"type": "Hash160", "value": tee_hash}]
    
    result = invoke_contract_test("addOracle", params)
    
    if result.get("result", {}).get("state") == "HALT":
        print("✅ Add oracle test invocation successful")
        print(f"   Gas consumed: {result['result'].get('gasconsumed', 'N/A')}")
        return True
    else:
        print("❌ Add oracle test invocation failed")
        print(f"   Error: {result.get('result', {}).get('exception', 'Unknown error')}")
        return False

def set_min_oracles():
    """Set minimum oracles to 1"""
    print("\n⚙️ Setting minimum oracles to 1...")
    
    params = [{"type": "Integer", "value": "1"}]
    
    result = invoke_contract_test("setMinOracles", params)
    
    if result.get("result", {}).get("state") == "HALT":
        print("✅ Set min oracles test invocation successful")
        print(f"   Gas consumed: {result['result'].get('gasconsumed', 'N/A')}")
        return True
    else:
        print("❌ Set min oracles test invocation failed")
        print(f"   Error: {result.get('result', {}).get('exception', 'Unknown error')}")
        return False

def verify_setup():
    """Verify the contract setup"""
    print("\n🔍 Verifying contract setup...")
    
    # Check oracle count
    result = invoke_contract_test("getOracleCount", [])
    if result.get("result", {}).get("stack", []):
        count = int(result["result"]["stack"][0].get("value", "0"))
        print(f"✅ Oracle count: {count}")
    
    # Check if TEE is oracle
    tee_hash = address_to_script_hash(TEE_ACCOUNT)
    params = [{"type": "Hash160", "value": tee_hash}]
    result = invoke_contract_test("isOracle", params)
    if result.get("result", {}).get("stack", []):
        is_oracle = result["result"]["stack"][0].get("value") == "1"
        print(f"✅ TEE account is oracle: {is_oracle}")
    
    # Check min oracles
    result = invoke_contract_test("getMinOracles", [])
    if result.get("result", {}).get("stack", []):
        min_oracles = int(result["result"]["stack"][0].get("value", "0"))
        print(f"✅ Minimum oracles: {min_oracles}")

def show_manual_commands():
    """Show manual commands for neo-cli"""
    print("\n📋 MANUAL NEO-CLI COMMANDS")
    print("=" * 50)
    print("Run these commands in neo-cli if automatic initialization fails:\n")
    
    print("1. Initialize contract:")
    print(f'   invoke {CONTRACT_HASH} initialize ["{MASTER_ACCOUNT}","{TEE_ACCOUNT}"]')
    print()
    
    print("2. Add TEE as oracle:")
    print(f'   invoke {CONTRACT_HASH} addOracle ["{TEE_ACCOUNT}"]')
    print()
    
    print("3. Set minimum oracles:")
    print(f'   invoke {CONTRACT_HASH} setMinOracles [1]')
    print()
    
    print("4. Verify setup:")
    print(f'   invoke {CONTRACT_HASH} getOracleCount []')
    print(f'   invoke {CONTRACT_HASH} isOracle ["{TEE_ACCOUNT}"]')
    print(f'   invoke {CONTRACT_HASH} getMinOracles []')

def main():
    """Main initialization process"""
    print("🚀 NEO PRICE FEED CONTRACT INITIALIZATION")
    print("=" * 50)
    print(f"Contract: {CONTRACT_HASH}")
    print(f"Network: Neo N3 TestNet")
    print(f"RPC: {RPC_ENDPOINT}")
    print()
    
    try:
        # Check if already initialized
        if check_contract_state():
            verify_setup()
            print("\n✅ Contract is already set up and ready to use!")
            return
        
        # Test invocations
        print("\n📝 Running test invocations...")
        print("Note: These are test calls to verify the methods work.")
        print("You'll need to sign and send the actual transactions.\n")
        
        # Initialize
        if not initialize_contract():
            show_manual_commands()
            return
        
        # Add oracle
        if not add_oracle():
            show_manual_commands()
            return
        
        # Set min oracles
        if not set_min_oracles():
            show_manual_commands()
            return
        
        # Show manual commands for actual execution
        show_manual_commands()
        
        print("\n🎯 NEXT STEPS:")
        print("1. Use neo-cli to execute the commands above")
        print("2. Sign each transaction with your wallet")
        print("3. Wait for confirmations after each transaction")
        print("4. Run this script again to verify setup")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        show_manual_commands()

if __name__ == "__main__":
    main()