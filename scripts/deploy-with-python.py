#!/usr/bin/env python3
"""
Deploy Neo N3 Smart Contract using Python neo3-boa
"""

import json
import requests
import base64
import hashlib
from typing import Optional

print("🚀 Neo N3 Contract Deployment Tool")
print("=" * 50)

# Configuration
TESTNET_RPC = "http://seed1t5.neo.org:20332"
MASTER_WIF = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb"
MASTER_ADDRESS = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"

def make_rpc_call(method: str, params: list = None) -> Optional[dict]:
    """Make RPC call to Neo node"""
    if params is None:
        params = []
    
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    try:
        response = requests.post(TESTNET_RPC, json=payload, timeout=30)
        result = response.json()
        
        if "error" in result:
            print(f"❌ RPC Error: {result['error']}")
            return None
            
        return result.get("result")
    except Exception as e:
        print(f"❌ Network Error: {e}")
        return None

def check_testnet_connection():
    """Check if we can connect to TestNet"""
    print("🌐 Checking TestNet connection...")
    
    version = make_rpc_call("getversion")
    if version:
        print(f"✅ Connected to Neo N3 TestNet")
        print(f"   Protocol: {version['protocol']['protocol']}")
        print(f"   Network: {version['protocol']['network']}")
        return True
    else:
        print("❌ Failed to connect to TestNet")
        return False

def check_account_balance():
    """Check account balance"""
    print(f"\n💰 Checking account balance for {MASTER_ADDRESS}...")
    
    balance = make_rpc_call("getnep17balances", [MASTER_ADDRESS])
    if balance and "balance" in balance:
        print("   Account balances:")
        for b in balance["balance"]:
            asset_hash = b["assethash"]
            amount = int(b["amount"])
            
            # Convert known assets
            if asset_hash == "0xd2a4cff31913016155e38e474a2c06d08be276cf":  # GAS
                gas_amount = amount / 100000000  # 8 decimals
                print(f"   - GAS: {gas_amount}")
                if gas_amount < 10:
                    print("   ⚠️  Warning: Less than 10 GAS available for deployment")
                    return False
            elif asset_hash == "0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5":  # NEO
                neo_amount = amount  # 0 decimals
                print(f"   - NEO: {neo_amount}")
        
        return True
    else:
        print("❌ Failed to check balance")
        return False

def prepare_deployment_transaction():
    """Prepare deployment transaction data"""
    print("\n📄 Preparing deployment transaction...")
    
    try:
        # Read contract files
        with open("src/PriceFeed.Contracts/PriceFeed.Oracle.nef", "rb") as f:
            nef_bytes = f.read()
        
        with open("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json", "r") as f:
            manifest = json.load(f)
        
        print(f"✅ Contract files loaded")
        print(f"   NEF size: {len(nef_bytes)} bytes")
        print(f"   Contract name: {manifest.get('name', 'Unknown')}")
        
        # Create deployment script
        nef_hex = nef_bytes.hex()
        manifest_json = json.dumps(manifest, separators=(',', ':'))
        
        # Since we can't sign transactions without proper libraries,
        # let's create the deployment data that can be used with Neo-CLI
        deployment_data = {
            "nef_hex": nef_hex,
            "manifest_json": manifest_json,
            "deployer": MASTER_ADDRESS,
            "wif": MASTER_WIF
        }
        
        # Save for manual deployment
        with open("deployment_transaction.json", "w") as f:
            json.dump(deployment_data, f, indent=2)
        
        print(f"💾 Deployment data saved to: deployment_transaction.json")
        return True
        
    except Exception as e:
        print(f"❌ Error preparing deployment: {e}")
        return False

def provide_deployment_instructions():
    """Provide step-by-step deployment instructions"""
    print("\n🛠️ DEPLOYMENT INSTRUCTIONS")
    print("=" * 50)
    
    print("\n📋 Since we need proper Neo SDK for transaction signing,")
    print("   here are your best options for deployment:")
    
    print("\n🌐 OPTION 1: Web Deployment (Recommended)")
    print("   1. Go to: https://onegate.space/deploy")
    print("   2. Click 'Connect Wallet' → 'Import Private Key'")
    print(f"   3. Enter WIF: {MASTER_WIF}")
    print("   4. Switch to TestNet network")
    print("   5. Upload NEF file: src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    print("   6. Upload Manifest: src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
    print("   7. Click 'Deploy' and confirm transaction")
    print("   8. Copy the contract hash from the result")
    
    print("\n🔌 OPTION 2: NeoLine Browser Extension")
    print("   1. Install: https://neoline.io/")
    print("   2. Import account with your private key")
    print("   3. Switch to TestNet")
    print("   4. Use dApp deployment feature")
    
    print("\n💻 OPTION 3: Neo-CLI (if you have it installed)")
    print("   1. Download Neo-CLI from GitHub releases")
    print("   2. Start with: ./neo-cli --network testnet")
    print(f"   3. Run: import key {MASTER_WIF}")
    print("   4. Run: open wallet")
    print("   5. Run: deploy src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    
    print("\n📝 AFTER DEPLOYMENT:")
    print("   1. Copy your contract hash (starts with 0x)")
    print("   2. Update src/PriceFeed.Console/appsettings.json:")
    print('      "ContractScriptHash": "0xYOUR_CONTRACT_HASH"')
    print("   3. Initialize the contract:")
    print('      invoke CONTRACT_HASH initialize ["NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX","NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]')
    print('      invoke CONTRACT_HASH addOracle ["NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]')
    print('      invoke CONTRACT_HASH setMinOracles [1]')
    print("   4. Test the workflow:")
    print("      dotnet run --project src/PriceFeed.Console --skip-health-checks")

def main():
    """Main deployment process"""
    print("Starting Neo N3 contract deployment process...\n")
    
    # Check prerequisites
    if not check_testnet_connection():
        return False
    
    if not check_account_balance():
        return False
    
    if not prepare_deployment_transaction():
        return False
    
    # Provide deployment instructions
    provide_deployment_instructions()
    
    print("\n✅ Deployment preparation complete!")
    print("   Choose one of the deployment methods above to deploy your contract.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Deployment cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)