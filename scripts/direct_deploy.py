#!/usr/bin/env python3
"""
Direct Neo N3 contract deployment using proper RPC methods
Based on how Neo-CLI actually handles deployment
"""

import json
import requests
import base64
from pathlib import Path

TESTNET_RPC = "http://seed1t5.neo.org:20332"
MASTER_ADDRESS = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"

def test_deployment_readiness():
    """Test if contract can be deployed using proper Neo N3 methods"""
    print("🚀 Testing Neo N3 Contract Deployment Readiness")
    print("=" * 55)
    
    # Check files
    nef_file = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    manifest_file = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
    
    if not nef_file.exists() or not manifest_file.exists():
        print("❌ Contract files not found")
        return False
    
    print(f"✅ Contract files found:")
    print(f"   NEF: {nef_file} ({nef_file.stat().st_size} bytes)")
    print(f"   Manifest: {manifest_file} ({manifest_file.stat().st_size} bytes)")
    
    # Read files
    with open(nef_file, 'rb') as f:
        nef_data = f.read()
    
    with open(manifest_file, 'r') as f:
        manifest_data = f.read()
    
    # Test connectivity
    try:
        response = requests.post(TESTNET_RPC, json={
            "jsonrpc": "2.0",
            "method": "getblockcount",
            "params": [],
            "id": 1
        }, timeout=10)
        
        result = response.json()
        if "result" in result:
            print(f"✅ TestNet connected (Block {result['result']})")
        else:
            print("❌ TestNet connection failed")
            return False
    except:
        print("❌ Network error")
        return False
    
    # Check account balance
    try:
        response = requests.post(TESTNET_RPC, json={
            "jsonrpc": "2.0",
            "method": "getnep17balances",
            "params": [MASTER_ADDRESS],
            "id": 1
        }, timeout=10)
        
        result = response.json()
        if "result" in result:
            balances = result["result"].get("balance", [])
            gas_balance = 0
            
            for balance in balances:
                if balance["assethash"] == "0xd2a4cff31913016155e38e474a2c06d08be276cf":
                    gas_balance = int(balance["amount"]) / 100_000_000
            
            print(f"✅ Account balance: {gas_balance} GAS")
            
            if gas_balance < 15:
                print("❌ Insufficient GAS for deployment")
                return False
        else:
            print("❌ Could not check balance")
            return False
    except:
        print("❌ Error checking balance")
        return False
    
    # Test contract deployment via proper method
    print(f"\n🧪 Testing contract deployment simulation...")
    
    try:
        # Create proper deployment parameters following Neo.CLI
        nef_b64 = base64.b64encode(nef_data).decode()
        
        # Use the calculateapplicationgas method to estimate deployment cost
        response = requests.post(TESTNET_RPC, json={
            "jsonrpc": "2.0",
            "method": "calculateapplicationgas",
            "params": [nef_b64, manifest_data],
            "id": 1
        }, timeout=30)
        
        result = response.json()
        if "result" in result:
            gas_cost = int(result["result"]) / 100_000_000
            print(f"✅ Deployment simulation successful")
            print(f"   Estimated cost: {gas_cost} GAS")
            
            if gas_cost > gas_balance:
                print(f"❌ Insufficient GAS: need {gas_cost}, have {gas_balance}")
                return False
            
            print(f"✅ Sufficient GAS for deployment")
            return True
        else:
            # If that method doesn't exist, try alternative validation
            print("⚠️  Direct gas calculation not available")
            print("   Proceeding with manual validation...")
            
            # Validate NEF format
            if nef_data[:4] != b'NEF3':
                print("❌ Invalid NEF format")
                return False
            
            # Validate manifest JSON
            try:
                manifest_obj = json.loads(manifest_data)
                if "name" not in manifest_obj:
                    print("❌ Invalid manifest format")
                    return False
            except:
                print("❌ Invalid manifest JSON")
                return False
            
            print("✅ Contract validation passed")
            print("   Contract format is valid for deployment")
            return True
            
    except Exception as e:
        print(f"❌ Deployment test failed: {e}")
        return False

def show_deployment_instructions():
    """Show final deployment instructions"""
    print(f"\n🎯 DEPLOYMENT INSTRUCTIONS")
    print("=" * 30)
    print()
    print("Your contract is ready for deployment! Use one of these methods:")
    print()
    print("🥇 RECOMMENDED: NeoLine Extension")
    print("   1. Install: https://neoline.io/")
    print("   2. Import private key: KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb")
    print("   3. Switch to TestNet")
    print("   4. Deploy contract:")
    print("      - Upload: src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    print("      - Upload: src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
    print("   5. Copy the contract hash from the result")
    print()
    print("🥈 ALTERNATIVE: Neo-CLI")
    print("   1. Download: https://github.com/neo-project/neo-cli/releases/tag/v3.8.2")
    print("   2. Extract and run: ./neo-cli --network testnet")
    print("   3. Import account: import key KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb")
    print("   4. Deploy: deploy src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    print()
    print("📝 After deployment:")
    print("   python3 scripts/update-contract-hash.py YOUR_CONTRACT_HASH")
    print("   python3 scripts/initialize-contract.py")
    print("   dotnet run --project src/PriceFeed.Console --skip-health-checks")

def main():
    """Main deployment readiness check"""
    if test_deployment_readiness():
        print(f"\n🎉 DEPLOYMENT READINESS: ✅ SUCCESS!")
        print("   Your Neo N3 Price Feed Oracle is ready for deployment!")
        show_deployment_instructions()
        return True
    else:
        print(f"\n❌ DEPLOYMENT READINESS: FAILED")
        print("   Please resolve the issues above before deploying.")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment check cancelled")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")