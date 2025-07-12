#!/usr/bin/env python3
"""
Check if everything is ready for deployment and provide instructions
"""

import json
import requests
import os
from pathlib import Path

print("🎯 Neo N3 Contract Deployment Readiness Check")
print("=" * 60)

# Configuration
TESTNET_RPC = "http://seed1t5.neo.org:20332"
MASTER_ADDRESS = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"
MASTER_WIF = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb"

def check_files():
    """Check if all required files exist"""
    print("📁 Checking contract files...")
    
    nef_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    manifest_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
    
    if nef_path.exists():
        size = nef_path.stat().st_size
        print(f"✅ NEF file found: {nef_path} ({size} bytes)")
    else:
        print(f"❌ NEF file missing: {nef_path}")
        return False
    
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        print(f"✅ Manifest file found: {manifest_path}")
        print(f"   Contract name: {manifest.get('name', 'Unknown')}")
    else:
        print(f"❌ Manifest file missing: {manifest_path}")
        return False
    
    return True

def check_network():
    """Check TestNet connectivity"""
    print("\n🌐 Checking TestNet connectivity...")
    
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "getblockcount",
            "params": [],
            "id": 1
        }
        
        response = requests.post(TESTNET_RPC, json=payload, timeout=10)
        result = response.json()
        
        if "result" in result:
            block_count = result["result"]
            print(f"✅ TestNet connection successful")
            print(f"   Current block height: {block_count}")
            return True
        else:
            print(f"❌ TestNet RPC error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False

def check_account():
    """Check account balance"""
    print(f"\n💰 Checking account balance for {MASTER_ADDRESS}...")
    
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "getnep17balances",
            "params": [MASTER_ADDRESS],
            "id": 1
        }
        
        response = requests.post(TESTNET_RPC, json=payload, timeout=10)
        result = response.json()
        
        if "result" in result and "balance" in result["result"]:
            balances = result["result"]["balance"]
            gas_balance = 0
            neo_balance = 0
            
            for balance in balances:
                asset_hash = balance["assethash"]
                amount = int(balance["amount"])
                
                if asset_hash == "0xd2a4cff31913016155e38e474a2c06d08be276cf":  # GAS
                    gas_balance = amount / 100000000
                elif asset_hash == "0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5":  # NEO
                    neo_balance = amount
            
            print(f"✅ Account balances:")
            print(f"   NEO: {neo_balance}")
            print(f"   GAS: {gas_balance}")
            
            if gas_balance >= 10:
                print("✅ Sufficient GAS for deployment")
                return True
            else:
                print("❌ Insufficient GAS for deployment (need at least 10 GAS)")
                return False
        else:
            print(f"❌ Failed to get balance: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        return False

def provide_deployment_options():
    """Provide deployment options"""
    print("\n🚀 DEPLOYMENT OPTIONS")
    print("=" * 30)
    
    print("\n🥇 RECOMMENDED: OneGate Web Deployment")
    print("   This is the easiest and most reliable method:")
    print()
    print("   1. 🌐 Go to: https://onegate.space/deploy")
    print("   2. 🔑 Click 'Connect Wallet' → 'Import Private Key'")
    print(f"   3. 📝 Enter your WIF: {MASTER_WIF}")
    print("   4. 🌍 Switch network to 'TestNet'")
    print("   5. 📄 Upload NEF file: src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    print("   6. 📄 Upload Manifest: src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
    print("   7. 🚀 Click 'Deploy Contract' button")
    print("   8. ✅ Confirm the transaction")
    print("   9. 📋 Copy the contract hash from the result")
    
    print("\n🥈 ALTERNATIVE: NeoLine Browser Extension")
    print("   If you prefer using a browser extension:")
    print()
    print("   1. 🔌 Install NeoLine: https://neoline.io/")
    print("   2. 🔑 Import your account with the private key")
    print("   3. 🌍 Switch to TestNet")
    print("   4. 🚀 Use the deployment feature")
    
    print("\n🥉 ADVANCED: Neo-CLI")
    print("   For command-line enthusiasts:")
    print()
    print("   1. 📥 Download: https://github.com/neo-project/neo-cli/releases")
    print("   2. 🚀 Run: ./neo-cli --network testnet")
    print(f"   3. 🔑 Run: import key {MASTER_WIF}")
    print("   4. 📁 Run: deploy src/PriceFeed.Contracts/PriceFeed.Oracle.nef")

def provide_post_deployment_steps():
    """Provide post-deployment steps"""
    print("\n📝 AFTER DEPLOYMENT - IMPORTANT STEPS")
    print("=" * 45)
    
    print("\n1️⃣ UPDATE CONFIGURATION")
    print("   Edit src/PriceFeed.Console/appsettings.json:")
    print('   Change: "ContractScriptHash": "0xYOUR_CONTRACT_HASH_HERE"')
    print('   To: "ContractScriptHash": "0xYOUR_ACTUAL_CONTRACT_HASH"')
    
    print("\n2️⃣ INITIALIZE THE CONTRACT")
    print("   Run these commands in your deployment tool:")
    print()
    print('   invoke CONTRACT_HASH initialize ["NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX","NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]')
    print('   invoke CONTRACT_HASH addOracle ["NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]')
    print('   invoke CONTRACT_HASH setMinOracles [1]')
    
    print("\n3️⃣ TEST THE WORKFLOW")
    print("   Run the price feed to verify everything works:")
    print()
    print("   dotnet run --project src/PriceFeed.Console --skip-health-checks")
    
    print("\n4️⃣ VERIFY ON EXPLORER")
    print("   Check your deployment on TestNet explorer:")
    print("   https://testnet.explorer.onegate.space/")

def main():
    """Main check process"""
    print("Checking deployment readiness...\n")
    
    all_good = True
    
    # Check files
    if not check_files():
        all_good = False
    
    # Check network
    if not check_network():
        all_good = False
    
    # Check account
    if not check_account():
        all_good = False
    
    if all_good:
        print("\n🎉 DEPLOYMENT READINESS: ✅ ALL SYSTEMS GO!")
        print("Your contract is ready for deployment!")
        
        provide_deployment_options()
        provide_post_deployment_steps()
        
        print("\n💡 QUICK START:")
        print("   → Go to https://onegate.space/deploy")
        print("   → Import your account and deploy!")
        
    else:
        print("\n❌ DEPLOYMENT READINESS: ISSUES FOUND")
        print("Please resolve the issues above before deploying.")
    
    return all_good

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment check cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")