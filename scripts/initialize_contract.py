#!/usr/bin/env python3
"""
Initialize the deployed price oracle contract
"""
import requests
import json
import sys

def rpc_call(method, params):
    """Make RPC call to Neo node"""
    url = "http://seed1t5.neo.org:20332"
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    response = requests.post(url, json=payload)
    return response.json()

def main():
    print("🚀 Price Oracle Contract Initialization")
    print("=" * 50)
    
    # Contract details
    contract_hash = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc"
    master_account = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"
    tee_account = "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"
    
    print(f"\n📋 Contract Details:")
    print(f"   Contract Hash: {contract_hash}")
    print(f"   Master Account: {master_account}")
    print(f"   TEE Account: {tee_account}")
    
    # Check if contract exists
    print("\n🔍 Checking contract state...")
    result = rpc_call("getcontractstate", [contract_hash])
    
    if "error" in result:
        print(f"❌ Contract not found: {result['error']['message']}")
        print("\n⚠️  The contract needs to be deployed first!")
        print("\nDEPLOYMENT OPTIONS:")
        print("1. Use Neo-CLI to deploy the contract")
        print("2. Use NeoLine browser extension")
        print("3. Wait for the previous deployment transaction to be confirmed")
        return
    
    print("✅ Contract found!")
    contract = result["result"]
    print(f"   Name: {contract['manifest']['name']}")
    
    # Show initialization commands
    print("\n📝 INITIALIZATION COMMANDS:")
    print("\nUse Neo-CLI or NeoLine to execute these commands:")
    
    print("\n1️⃣ Add Oracle Account:")
    print(f"   invoke {contract_hash} addOracle [\"{tee_account}\"]")
    
    print("\n2️⃣ Set Minimum Oracles to 1:")
    print(f"   invoke {contract_hash} setMinOracles [1]")
    
    print("\n3️⃣ Verify Oracle Status:")
    print(f"   invokefunction {contract_hash} isOracle [\"{tee_account}\"]")
    print(f"   invokefunction {contract_hash} getMinOracles")
    
    print("\n4️⃣ Test Price Update (after initialization):")
    print("   dotnet run --project src/PriceFeed.Console")
    
    # Create initialization script for Neo-CLI
    neo_cli_script = f"""# Neo-CLI Initialization Script
# Run these commands in Neo-CLI after opening your wallet

# Add oracle account
invoke {contract_hash} addOracle ["{tee_account}"]

# Set minimum oracles to 1
invoke {contract_hash} setMinOracles [1]

# Verify setup
invokefunction {contract_hash} isOracle ["{tee_account}"]
invokefunction {contract_hash} getMinOracles
"""
    
    with open("neo-cli-init.txt", "w") as f:
        f.write(neo_cli_script)
    
    print("\n✅ Neo-CLI script saved to: neo-cli-init.txt")
    
    # Test invoke functions
    print("\n🧪 Testing contract methods...")
    
    # Test getOwner
    result = rpc_call("invokefunction", [contract_hash, "getOwner", []])
    if result.get("result", {}).get("state") == "HALT":
        print("✅ getOwner() works")
    
    # Test getMinOracles
    result = rpc_call("invokefunction", [contract_hash, "getMinOracles", []])
    if result.get("result", {}).get("state") == "HALT":
        stack = result["result"].get("stack", [])
        if stack:
            min_oracles = int(stack[0].get("value", "0"))
            print(f"✅ getMinOracles() = {min_oracles}")
    
    print("\n🎯 Next Steps:")
    print("1. Initialize the contract using the commands above")
    print("2. Run the price oracle to test:")
    print("   dotnet run --project src/PriceFeed.Console")

if __name__ == "__main__":
    main()