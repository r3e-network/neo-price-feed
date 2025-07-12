#!/usr/bin/env python3
"""
Simple contract initialization check
"""

import json
import urllib.request
import urllib.error

# Configuration
RPC_ENDPOINT = "http://seed1t5.neo.org:20332"
CONTRACT_HASH = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc"
MASTER_ACCOUNT = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"
TEE_ACCOUNT = "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"

# Pre-calculated script hashes (to avoid base58 dependency)
MASTER_SCRIPT_HASH = "0x52c4d9e08e5ac0026dd4f1bc6b4e5bcd1cf1f70f"
TEE_SCRIPT_HASH = "0xb851b96c2de68c69e1c2c87cf89f0e7c5e3b3e93"

def rpc_call(method, params):
    """Make RPC call to Neo node"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(RPC_ENDPOINT, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"RPC Error: {e}")
        return None

def invoke_function(method, params=[]):
    """Invoke contract function"""
    return rpc_call("invokefunction", [CONTRACT_HASH, method, params])

def check_status():
    """Check contract initialization status"""
    print("🚀 NEO PRICE FEED CONTRACT STATUS")
    print("=" * 50)
    print(f"Contract: {CONTRACT_HASH}")
    print(f"Network: Neo N3 TestNet")
    print()
    
    # Check if initialized
    print("🔍 Checking initialization...")
    result = invoke_function("isInitialized")
    
    if result and result.get("result", {}).get("state") == "HALT":
        stack = result.get("result", {}).get("stack", [])
        if stack and stack[0].get("value") in ["1", 1, True]:
            print("✅ Contract is initialized")
            is_initialized = True
        else:
            print("❌ Contract is NOT initialized")
            is_initialized = False
    else:
        print("❌ Failed to check initialization")
        is_initialized = False
    
    if not is_initialized:
        print("\n📋 INITIALIZATION REQUIRED")
        print("=" * 40)
        print("\nRun these commands in neo-cli:\n")
        print(f'1. invoke {CONTRACT_HASH} initialize ["{MASTER_ACCOUNT}","{TEE_ACCOUNT}"]')
        print(f'2. invoke {CONTRACT_HASH} addOracle ["{TEE_ACCOUNT}"]')
        print(f'3. invoke {CONTRACT_HASH} setMinOracles [1]')
        return
    
    # Check oracle count
    print("\n🔍 Checking oracle configuration...")
    result = invoke_function("getOracleCount")
    if result and result.get("result", {}).get("state") == "HALT":
        stack = result.get("result", {}).get("stack", [])
        if stack:
            count = int(stack[0].get("value", "0"))
            print(f"📊 Oracle count: {count}")
    
    # Check min oracles
    result = invoke_function("getMinOracles")
    if result and result.get("result", {}).get("state") == "HALT":
        stack = result.get("result", {}).get("stack", [])
        if stack:
            min_oracles = int(stack[0].get("value", "0"))
            print(f"⚙️  Minimum oracles: {min_oracles}")
    
    # Test price query
    print("\n🔍 Testing price query...")
    params = [{"type": "String", "value": "BTCUSDT"}]
    result = invoke_function("getPrice", params)
    
    if result and result.get("result", {}).get("state") == "HALT":
        stack = result.get("result", {}).get("stack", [])
        if stack and stack[0].get("type") == "Integer":
            price = int(stack[0].get("value", "0"))
            if price > 0:
                print(f"💰 BTCUSDT price: {price}")
            else:
                print("📝 No price set for BTCUSDT yet")
    
    print("\n✅ Contract is ready!")
    print("\n🎯 Next: Run price feed service")
    print("   dotnet run --project src/PriceFeed.Console")

if __name__ == "__main__":
    try:
        check_status()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()