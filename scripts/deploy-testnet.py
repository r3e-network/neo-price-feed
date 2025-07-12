#!/usr/bin/env python3
"""
Neo N3 TestNet Contract Deployment Script
"""

import json
import sys
import time
from typing import Dict, Any

print("🚀 Neo N3 Smart Contract TestNet Deployment")
print("=" * 50)

# Configuration
TESTNET_RPC = "http://seed1t5.neo.org:20332"
MASTER_ADDRESS = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"
MASTER_WIF = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb"
TEE_ADDRESS = "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"

print("\n📋 Deployment Configuration:")
print(f"   Network: Neo N3 TestNet")
print(f"   RPC: {TESTNET_RPC}")
print(f"   Master Account: {MASTER_ADDRESS}")
print(f"   TEE Account: {TEE_ADDRESS}")

print("\n⚠️  IMPORTANT: Manual Deployment Required")
print("-" * 50)
print("Due to the complexity of Neo contract deployment, please follow these steps:")

print("\n📝 Step 1: Install Neo-CLI or Use Neo-GUI")
print("   Option A: Download Neo-CLI from https://github.com/neo-project/neo-cli/releases")
print("   Option B: Download Neo-GUI from https://github.com/neo-project/neo-gui/releases")
print("   Option C: Use Neo Web Wallet at https://neowallet.cn/ (TestNet)")

print("\n📝 Step 2: Import Your Master Account")
print(f"   - Use this WIF to import: {MASTER_WIF}")
print(f"   - Verify address shows as: {MASTER_ADDRESS}")
print(f"   - Ensure you have 50 NEO and 50 GAS on TestNet")

print("\n📝 Step 3: Deploy the Contract")
print("   For Neo-CLI:")
print("   ```")
print("   neo> open wallet master.json")
print("   neo> deploy ../src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
print("   ```")
print("   ")
print("   For Neo-GUI:")
print("   - Go to Advanced -> Deploy Contract")
print("   - Select NEF file: src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
print("   - Select Manifest: src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
print("   - Click Deploy")

print("\n📝 Step 4: Initialize the Contract")
print("   After deployment, you need to initialize with:")
print("   ```")
print(f"   invoke [CONTRACT_HASH] initialize [{MASTER_ADDRESS}, {TEE_ADDRESS}]")
print(f"   invoke [CONTRACT_HASH] addOracle [{TEE_ADDRESS}]")
print("   invoke [CONTRACT_HASH] setMinOracles [1]")
print("   ```")

print("\n📝 Step 5: Update Configuration")
print("   Update src/PriceFeed.Console/appsettings.json:")
print("   - Replace ContractScriptHash with your deployed contract hash")

print("\n🌐 Useful Links:")
print("   - TestNet Explorer: https://testnet.explorer.onegate.space/")
print("   - Neo Documentation: https://docs.neo.org/")
print("   - TestNet Faucet: https://neowish.ngd.network/ (if you need more GAS)")

print("\n💡 Alternative: Use NeoLine Chrome Extension")
print("   1. Install NeoLine from Chrome Web Store")
print("   2. Import your account using the WIF")
print("   3. Switch to TestNet")
print("   4. Use https://neo.org/deploy for web-based deployment")

# Generate deployment summary file
deployment_info = {
    "network": "Neo N3 TestNet",
    "rpc_endpoint": TESTNET_RPC,
    "master_account": {
        "address": MASTER_ADDRESS,
        "wif": MASTER_WIF
    },
    "tee_account": {
        "address": TEE_ADDRESS
    },
    "contract_files": {
        "nef": "src/PriceFeed.Contracts/PriceFeed.Oracle.nef",
        "manifest": "src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json"
    },
    "initialization_commands": [
        f"initialize [{MASTER_ADDRESS}, {TEE_ADDRESS}]",
        f"addOracle [{TEE_ADDRESS}]",
        "setMinOracles [1]"
    ],
    "deployment_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
}

with open("deployment-config.json", "w") as f:
    json.dump(deployment_info, f, indent=2)

print(f"\n💾 Deployment configuration saved to: deployment-config.json")
print("\n✅ Deployment preparation complete!")
print("   Please proceed with manual deployment using one of the methods above.")