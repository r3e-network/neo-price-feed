#!/usr/bin/env python3
"""
Generate deployment transaction data for manual submission
"""

import json
import base64
import hashlib

print("📄 Neo N3 Contract Deployment Transaction Generator")
print("=" * 60)

# Read contract files
try:
    with open("src/PriceFeed.Contracts/PriceFeed.Oracle.nef", "rb") as f:
        nef_bytes = f.read()
        nef_hex = nef_bytes.hex()
        
    with open("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json", "r") as f:
        manifest = json.load(f)
        manifest_str = json.dumps(manifest, separators=(',', ':'))
        
    print(f"\n✅ Contract files loaded successfully")
    print(f"   NEF size: {len(nef_bytes)} bytes")
    print(f"   Contract name: {manifest.get('name', 'Unknown')}")
    
    # Generate deployment script
    print("\n📝 Deployment Script (for Neo-CLI or compatible tools):")
    print("-" * 60)
    print("# Copy and paste these commands into Neo-CLI after opening your wallet:")
    print("")
    print("# Deploy command (single line):")
    print(f"deploy ./PriceFeed.Oracle.nef")
    print("")
    print("# Or if using invoke for manual deployment:")
    print("# This deploys the contract using system call")
    print(f"invoke 0xfffdc93764dbaddd97c48f252a53ea4643faa3fd deploy")
    print("")
    
    # Create deployment data file
    deployment_data = {
        "network": "testnet",
        "deployer": "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX",
        "contract_name": manifest.get('name', 'PriceFeed.Oracle'),
        "nef_size": len(nef_bytes),
        "manifest_size": len(manifest_str),
        "estimated_gas": "10-15 GAS",
        "initialization": {
            "step1": "initialize [\"NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX\",\"NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB\"]",
            "step2": "addOracle [\"NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB\"]",
            "step3": "setMinOracles [1]"
        }
    }
    
    with open("deployment-data.json", "w") as f:
        json.dump(deployment_data, f, indent=2)
        
    print("\n💾 Deployment data saved to: deployment-data.json")
    
    print("\n🌐 Web-based Deployment Options:")
    print("1. OneGate Deploy: https://onegate.space/deploy")
    print("2. Neo Playground: https://neo-playground.dev/")
    print("3. NeoTube Wallet: https://neotube.io/")
    
    print("\n📱 Mobile Options:")
    print("1. O3 Wallet (iOS/Android)")
    print("2. Neon Wallet Mobile")
    
    print("\n✅ All deployment data prepared successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("Make sure you're running from the project root directory")