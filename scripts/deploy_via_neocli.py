#!/usr/bin/env python3
"""
Deploy contract using Neo-CLI compatible approach
"""
import json
import requests
import time
import base64
from pathlib import Path

def main():
    print("🚀 Neo N3 Contract Deployment Guide")
    print("=" * 50)
    
    # Contract files
    nef_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    manifest_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
    
    if not nef_path.exists() or not manifest_path.exists():
        print("❌ Contract files not found!")
        return
    
    print("✅ Contract files found")
    print(f"   NEF: {nef_path.stat().st_size} bytes")
    print(f"   Manifest: {manifest_path.stat().st_size} bytes")
    
    # Read files
    nef_bytes = nef_path.read_bytes()
    manifest_json = manifest_path.read_text()
    
    # Base64 encode for easier handling
    nef_b64 = base64.b64encode(nef_bytes).decode()
    
    print("\n📋 DEPLOYMENT OPTIONS:")
    print("\n1️⃣ Neo-CLI Method (Recommended):")
    print("   1. Download Neo-CLI: https://github.com/neo-project/neo-cli/releases")
    print("   2. Extract and run: ./neo-cli")
    print("   3. Create wallet:")
    print("      neo> create wallet deploy.json")
    print("   4. Import private key:")
    print("      neo> import key KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb")
    print("   5. Open wallet:")
    print("      neo> open wallet deploy.json")
    print("   6. Deploy contract:")
    print(f"      neo> deploy {nef_path} {manifest_path}")
    
    print("\n2️⃣ NeoLine Browser Extension:")
    print("   1. Install NeoLine: https://neoline.io/")
    print("   2. Import private key: KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb")
    print("   3. Switch to TestNet")
    print("   4. Go to: https://neoline.io/deploy")
    print("   5. Upload the NEF and manifest files")
    print("   6. Deploy with ~11 GAS fee")
    
    print("\n3️⃣ Neo Toolkit (Visual Studio Code):")
    print("   1. Install: https://marketplace.visualstudio.com/items?itemName=ngd-seattle.neo-blockchain-toolkit")
    print("   2. Open the project in VS Code")
    print("   3. Right-click on the .nef file")
    print("   4. Select 'Deploy Contract'")
    
    print("\n📝 Contract Details:")
    print(f"   NEF size: {len(nef_bytes)} bytes")
    print(f"   Manifest size: {len(manifest_json)} bytes")
    print(f"   Estimated deployment cost: ~10.04 GAS")
    print(f"   Account: NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX")
    print(f"   Balance: 50 GAS")
    
    # Save deployment files for easy access
    deploy_dir = Path("deployment-files")
    deploy_dir.mkdir(exist_ok=True)
    
    # Copy files
    (deploy_dir / "PriceFeed.Oracle.nef").write_bytes(nef_bytes)
    (deploy_dir / "PriceFeed.Oracle.manifest.json").write_text(manifest_json)
    
    # Create deployment info
    deploy_info = {
        "network": "testnet",
        "account": {
            "address": "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX",
            "privateKey": "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb"
        },
        "contract": {
            "name": "PriceFeedOracle",
            "nef_size": len(nef_bytes),
            "manifest_size": len(manifest_json),
            "estimated_gas": 10.04
        },
        "rpc_endpoints": [
            "http://seed1t5.neo.org:20332",
            "http://seed2t5.neo.org:20332"
        ]
    }
    
    (deploy_dir / "deployment-info.json").write_text(json.dumps(deploy_info, indent=2))
    
    print(f"\n✅ Deployment files saved to: {deploy_dir.absolute()}")
    print("\n🎯 After deployment:")
    print("   1. Note the contract hash from the deployment transaction")
    print("   2. Update appsettings.json with the new contract hash")
    print("   3. Initialize the contract:")
    print("      - addOracle: NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB")
    print("      - setMinOracles: 1")
    print("   4. Test the oracle:")
    print("      dotnet run --project src/PriceFeed.Console")

if __name__ == "__main__":
    main()