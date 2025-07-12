#!/usr/bin/env python3
"""
Update contract hash in configuration after deployment
"""

import json
import sys
import re
from pathlib import Path

def update_contract_hash(contract_hash: str):
    """Update the contract hash in appsettings.json"""
    
    # Validate hash format
    if not contract_hash.startswith('0x'):
        contract_hash = '0x' + contract_hash
    
    if not re.match(r'^0x[a-fA-F0-9]{40}$', contract_hash):
        print(f"❌ Invalid contract hash format: {contract_hash}")
        print("   Expected format: 0x followed by 40 hex characters")
        return False
    
    # Path to appsettings.json
    config_path = Path("src/PriceFeed.Console/appsettings.json")
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    try:
        # Read current configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update contract hash
        old_hash = config.get("BatchProcessing", {}).get("ContractScriptHash", "")
        config["BatchProcessing"]["ContractScriptHash"] = contract_hash
        
        # Write updated configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Contract hash updated successfully!")
        print(f"   Old hash: {old_hash}")
        print(f"   New hash: {contract_hash}")
        print(f"   File: {config_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

def show_next_steps(contract_hash: str):
    """Show next steps after updating configuration"""
    print(f"\n🎯 NEXT STEPS:")
    print(f"=" * 30)
    
    print(f"\n1️⃣ Initialize your contract:")
    print(f'   invoke {contract_hash} initialize ["NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX","NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]')
    print(f'   invoke {contract_hash} addOracle ["NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]')
    print(f'   invoke {contract_hash} setMinOracles [1]')
    
    print(f"\n2️⃣ Test your oracle:")
    print(f"   dotnet run --project src/PriceFeed.Console --skip-health-checks")
    
    print(f"\n3️⃣ View on explorer:")
    print(f"   https://testnet.explorer.onegate.space/contractinfo/{contract_hash}")
    
    print(f"\n🎉 Your Neo N3 Price Feed Oracle is ready to go live!")

def main():
    """Main function"""
    print("🔧 Neo N3 Contract Hash Updater")
    print("=" * 40)
    
    if len(sys.argv) != 2:
        print("\n❌ Usage: python3 update-contract-hash.py <CONTRACT_HASH>")
        print("\nExample:")
        print("   python3 update-contract-hash.py 0x1234567890abcdef1234567890abcdef12345678")
        print("\nOr without 0x prefix:")
        print("   python3 update-contract-hash.py 1234567890abcdef1234567890abcdef12345678")
        return
    
    contract_hash = sys.argv[1].strip()
    
    print(f"Updating contract hash to: {contract_hash}")
    
    if update_contract_hash(contract_hash):
        show_next_steps(contract_hash)
    else:
        print("\n❌ Failed to update contract hash")
        sys.exit(1)

if __name__ == "__main__":
    main()