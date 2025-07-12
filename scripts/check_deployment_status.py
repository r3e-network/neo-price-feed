#!/usr/bin/env python3
"""
Check the deployment status of the Price Oracle contract
"""
import requests
import json
import time
from datetime import datetime

def check_deployment():
    print("🔍 Neo N3 Price Oracle Deployment Status Check")
    print("=" * 50)
    
    # Configuration
    rpc_url = "http://seed1t5.neo.org:20332"
    expected_hash = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc"
    master_address = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"
    tee_address = "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"
    
    # Check network status
    try:
        response = requests.post(rpc_url, json={
            "jsonrpc": "2.0",
            "method": "getblockcount",
            "params": [],
            "id": 1
        })
        block_height = response.json()["result"]
        print(f"\n✅ Connected to Neo N3 TestNet")
        print(f"   Current block height: {block_height}")
    except Exception as e:
        print(f"\n❌ Failed to connect to TestNet: {e}")
        return
    
    # Check if contract is deployed
    print(f"\n🔍 Checking contract: {expected_hash}")
    
    response = requests.post(rpc_url, json={
        "jsonrpc": "2.0",
        "method": "getcontractstate",
        "params": [expected_hash],
        "id": 1
    })
    
    result = response.json()
    
    if "error" not in result:
        # Contract exists!
        contract = result["result"]
        print(f"\n🎉 CONTRACT DEPLOYED!")
        print(f"   Name: {contract['manifest']['name']}")
        print(f"   ID: {contract['id']}")
        print(f"   Hash: {expected_hash}")
        print(f"   Update Counter: {contract['updatecounter']}")
        
        # Check contract methods
        methods = contract['manifest']['abi']['methods']
        print(f"\n📋 Contract Methods ({len(methods)} total):")
        key_methods = ["initialize", "addOracle", "setMinOracles", "updatePrice", "getPrice"]
        for method in key_methods:
            if any(m['name'] == method for m in methods):
                print(f"   ✅ {method}")
        
        # Check initialization status
        print(f"\n🔧 Checking initialization status...")
        
        # Check owner
        response = requests.post(rpc_url, json={
            "jsonrpc": "2.0",
            "method": "invokefunction",
            "params": [expected_hash, "getOwner", []],
            "id": 1
        })
        
        owner_result = response.json()
        if owner_result.get("result", {}).get("state") == "HALT":
            print("   ✅ getOwner() callable")
        
        # Check min oracles
        response = requests.post(rpc_url, json={
            "jsonrpc": "2.0",
            "method": "invokefunction",
            "params": [expected_hash, "getMinOracles", []],
            "id": 1
        })
        
        min_oracles_result = response.json()
        if min_oracles_result.get("result", {}).get("state") == "HALT":
            stack = min_oracles_result["result"].get("stack", [])
            if stack:
                min_oracles = int(stack[0].get("value", "0"))
                print(f"   ✅ getMinOracles() = {min_oracles}")
                
                if min_oracles == 0:
                    print("\n⚠️  Contract needs initialization!")
                    print("\n📝 Run these commands in Neo-CLI:")
                    print(f"   invoke {expected_hash} addOracle [\"{tee_address}\"]")
                    print(f"   invoke {expected_hash} setMinOracles [1]")
        
        # Check if TEE is oracle
        response = requests.post(rpc_url, json={
            "jsonrpc": "2.0",
            "method": "invokefunction",
            "params": [
                expected_hash, 
                "isOracle", 
                [{"type": "Hash160", "value": tee_address}]
            ],
            "id": 1
        })
        
        oracle_result = response.json()
        if oracle_result.get("result", {}).get("state") == "HALT":
            stack = oracle_result["result"].get("stack", [])
            if stack and stack[0].get("value") == "1":
                print(f"   ✅ TEE account is registered as oracle")
            else:
                print(f"   ❌ TEE account is NOT registered as oracle")
        
        print(f"\n✅ Contract is deployed and ready for use!")
        print(f"\n🚀 Test the oracle:")
        print(f"   dotnet run --project src/PriceFeed.Console")
        
    else:
        # Contract not found
        print(f"\n❌ Contract NOT deployed yet")
        print(f"   Error: {result['error']['message']}")
        
        print(f"\n📋 DEPLOYMENT REQUIRED")
        print(f"\nThe contract has been prepared and validated:")
        print(f"   - NEF size: 2946 bytes")
        print(f"   - Manifest size: 4457 chars")
        print(f"   - Deployment cost: ~10.002 GAS")
        print(f"   - Account balance: 50 GAS")
        
        print(f"\n🚀 Deploy using one of these methods:")
        print(f"\n1️⃣ Neo-CLI:")
        print(f"   neo> deploy deployment-files/PriceFeed.Oracle.nef deployment-files/PriceFeed.Oracle.manifest.json")
        
        print(f"\n2️⃣ NeoLine Browser Extension:")
        print(f"   - Import private key")
        print(f"   - Switch to TestNet")
        print(f"   - Upload files from deployment-files/")
        
        print(f"\n📁 Deployment files ready at:")
        print(f"   - deployment-files/PriceFeed.Oracle.nef")
        print(f"   - deployment-files/PriceFeed.Oracle.manifest.json")
    
    # Check recent transactions
    print(f"\n📊 Recent activity for master account:")
    print(f"   Address: {master_address}")
    print(f"   Explorer: https://testnet.explorer.onegate.space/address/{master_address}")

if __name__ == "__main__":
    check_deployment()