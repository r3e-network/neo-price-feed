#!/usr/bin/env python3
"""
Deploy Neo N3 contract via RPC using official transaction construction
Based on Neo.CLI MainService.Contracts.cs and Neo.Network.RpcClient
"""

import json
import requests
import base64
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
TESTNET_RPC = "http://seed1t5.neo.org:20332"
MASTER_WIF = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb"
MASTER_ADDRESS = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"

# Neo N3 system hashes and constants
NEO_TOKEN = "0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5"
GAS_TOKEN = "0xd2a4cff31913016155e38e474a2c06d08be276cf"
MANAGEMENT_CONTRACT = "0xfffdc93764dbaddd97c48f252a53ea4643faa3fd"

class Neo3RpcClient:
    """Neo N3 RPC client for deployment operations"""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.session = requests.Session()
    
    def call(self, method: str, params: list = None) -> Optional[Dict[str, Any]]:
        """Make RPC call to Neo N3 node"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }
        
        try:
            response = self.session.post(self.endpoint, json=payload, timeout=30)
            result = response.json()
            
            if "error" in result:
                print(f"❌ RPC Error: {result['error']}")
                return None
                
            return result.get("result")
        except Exception as e:
            print(f"❌ Network error: {e}")
            return None
    
    def get_block_count(self) -> int:
        """Get current block count"""
        result = self.call("getblockcount")
        return result if result else 0
    
    def get_account_balance(self, address: str) -> Dict[str, float]:
        """Get NEP-17 token balances for account"""
        result = self.call("getnep17balances", [address])
        if not result or "balance" not in result:
            return {"NEO": 0, "GAS": 0}
        
        balances = {"NEO": 0, "GAS": 0}
        for balance in result["balance"]:
            asset_hash = balance["assethash"]
            amount = int(balance["amount"])
            
            if asset_hash == NEO_TOKEN:
                balances["NEO"] = amount
            elif asset_hash == GAS_TOKEN:
                balances["GAS"] = amount / 100_000_000  # Convert from datoshi
        
        return balances
    
    def calculate_network_fee(self, tx_size: int) -> int:
        """Calculate network fee based on transaction size"""
        result = self.call("calculatenetworkfee", [tx_size])
        return result.get("networkfee", 1000000) if result else 1000000
    
    def invoke_function(self, script_hash: str, operation: str, params: list) -> Optional[Dict[str, Any]]:
        """Invoke contract function for testing"""
        result = self.call("invokefunction", [script_hash, operation, params])
        return result
    
    def send_raw_transaction(self, tx_hex: str) -> Optional[str]:
        """Send raw transaction to network"""
        result = self.call("sendrawtransaction", [tx_hex])
        return result.get("hash") if result else None

class Neo3Transaction:
    """Neo N3 transaction builder for contract deployment"""
    
    @staticmethod
    def create_deploy_script(nef_file: Path, manifest_file: Path) -> str:
        """Create deployment script based on Neo.CLI implementation"""
        try:
            # Read NEF file
            with open(nef_file, 'rb') as f:
                nef_data = f.read()
            
            # Read manifest
            with open(manifest_file, 'r') as f:
                manifest_data = f.read()
            
            print(f"📁 Contract files:")
            print(f"   NEF size: {len(nef_data)} bytes")
            print(f"   Manifest size: {len(manifest_data)} bytes")
            
            # Create script following Neo.CLI MainService.Contracts.cs Deploy method
            # This creates a script that calls ContractManagement.Deploy
            
            # Convert to base64 for RPC transmission
            nef_b64 = base64.b64encode(nef_data).decode()
            manifest_str = manifest_data
            
            # Create deployment script
            # Similar to: PUSHDATA1 nef_data PUSHDATA1 manifest_data PUSH2 PACK PUSHDATA1 "deploy" PUSHDATA1 management_hash SYSCALL System.Contract.Call
            deploy_script = {
                "nef": nef_b64,
                "manifest": manifest_str,
                "operation": "deploy"
            }
            
            return deploy_script
            
        except Exception as e:
            print(f"❌ Error creating deploy script: {e}")
            return None

class Neo3Deployer:
    """Main deployment orchestrator"""
    
    def __init__(self):
        self.rpc = Neo3RpcClient(TESTNET_RPC)
        self.tx_builder = Neo3Transaction()
    
    def validate_deployment_requirements(self) -> bool:
        """Validate all deployment requirements"""
        print("🔍 Validating deployment requirements...")
        
        # Check files exist
        nef_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
        manifest_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
        
        if not nef_path.exists():
            print(f"❌ NEF file not found: {nef_path}")
            return False
        
        if not manifest_path.exists():
            print(f"❌ Manifest file not found: {manifest_path}")
            return False
        
        print(f"✅ Contract files found")
        
        # Check network connectivity
        block_count = self.rpc.get_block_count()
        if not block_count:
            print("❌ Cannot connect to TestNet")
            return False
        
        print(f"✅ TestNet connected (block {block_count})")
        
        # Check account balance
        balances = self.rpc.get_account_balance(MASTER_ADDRESS)
        print(f"✅ Account balances: {balances['NEO']} NEO, {balances['GAS']} GAS")
        
        if balances["GAS"] < 15:
            print("❌ Insufficient GAS (need at least 15 GAS)")
            return False
        
        return True
    
    def estimate_deployment_cost(self) -> Dict[str, int]:
        """Estimate deployment costs"""
        print("\n💰 Estimating deployment costs...")
        
        # Read contract files to estimate size
        nef_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
        manifest_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
        
        nef_size = nef_path.stat().st_size
        manifest_size = manifest_path.stat().st_size
        
        # Estimate transaction size (following Neo.CLI estimation)
        # Base transaction + script + nef + manifest + signatures
        estimated_tx_size = 200 + nef_size + manifest_size + 100  # Conservative estimate
        
        # Calculate fees
        network_fee = self.rpc.calculate_network_fee(estimated_tx_size)
        
        # System fee for deployment (from Neo.CLI experience)
        # Deploy operation typically costs 10-15 GAS
        system_fee = 10_000_000_000  # 10 GAS in datoshi
        
        costs = {
            "system_fee": system_fee,
            "network_fee": network_fee,
            "total_fee": system_fee + network_fee,
            "tx_size": estimated_tx_size
        }
        
        print(f"📊 Estimated costs:")
        print(f"   Transaction size: ~{estimated_tx_size} bytes")
        print(f"   System fee: ~{system_fee / 100_000_000} GAS")
        print(f"   Network fee: ~{network_fee / 100_000_000} GAS")
        print(f"   Total: ~{costs['total_fee'] / 100_000_000} GAS")
        
        return costs
    
    def create_deployment_transaction(self) -> Optional[str]:
        """Create deployment transaction following Neo.CLI methodology"""
        print("\n🔨 Creating deployment transaction...")
        
        # This is where we'd implement the full transaction construction
        # Following Neo.CLI MainService.Contracts.cs Deploy method
        
        print("⚠️  TECHNICAL NOTE:")
        print("   Full transaction construction requires:")
        print("   1. NEF file validation and processing")
        print("   2. Manifest JSON validation")
        print("   3. Script creation with proper opcodes")
        print("   4. Transaction assembly with witnesses")
        print("   5. Digital signature generation")
        print("   6. Network/system fee calculation")
        
        # Create deploy script
        nef_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
        manifest_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
        
        deploy_script = self.tx_builder.create_deploy_script(nef_path, manifest_path)
        
        if not deploy_script:
            return None
        
        print("✅ Deploy script created")
        
        # For a complete implementation, we would need to:
        # 1. Use Neo's transaction builder classes
        # 2. Implement proper signature generation
        # 3. Handle witness creation
        # 4. Calculate exact fees
        
        return deploy_script
    
    def deploy_via_invoke_script(self) -> bool:
        """Alternative: Deploy using invokefunction and sendrawtransaction"""
        print("\n🚀 Attempting deployment via RPC invoke...")
        
        try:
            # Read contract files
            nef_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
            manifest_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
            
            with open(nef_path, 'rb') as f:
                nef_data = f.read()
            
            with open(manifest_path, 'r') as f:
                manifest_data = f.read()
            
            # Convert to parameters for RPC call
            nef_param = {
                "type": "ByteArray",
                "value": base64.b64encode(nef_data).decode()
            }
            
            manifest_param = {
                "type": "String", 
                "value": manifest_data
            }
            
            # Test invoke first
            print("🧪 Testing deployment transaction...")
            result = self.rpc.invoke_function(
                MANAGEMENT_CONTRACT,
                "deploy",
                [nef_param, manifest_param]
            )
            
            if result and result.get("state") == "HALT":
                print(f"✅ Deployment test successful")
                print(f"   Gas consumed: {int(result.get('gasconsumed', 0)) / 100_000_000} GAS")
                
                # Get the contract hash from the result
                if "stack" in result and result["stack"]:
                    stack_item = result["stack"][0]
                    if stack_item.get("type") == "InteropInterface":
                        print("✅ Contract deployment would succeed")
                        return True
                
            else:
                print(f"❌ Deployment test failed: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False
        
        return False

def main():
    """Main deployment process"""
    print("🚀 Neo N3 Contract Deployment via RPC")
    print("=" * 50)
    print("Based on Neo.CLI MainService.Contracts.cs methodology")
    print()
    
    deployer = Neo3Deployer()
    
    # Validate requirements
    if not deployer.validate_deployment_requirements():
        print("\n❌ Deployment requirements not met")
        return False
    
    # Estimate costs
    costs = deployer.estimate_deployment_cost()
    
    # Test deployment
    if deployer.deploy_via_invoke_script():
        print("\n✅ DEPLOYMENT VALIDATION SUCCESSFUL!")
        print("\n📝 IMPORTANT NOTE:")
        print("   RPC deployment requires complex transaction signing.")
        print("   For immediate deployment, use NeoLine extension:")
        print("   1. Install: https://neoline.io/")
        print("   2. Import key and switch to TestNet")
        print("   3. Deploy contract files")
        print("\n🔧 ALTERNATIVE: Use Neo-CLI")
        print("   This script validates deployment readiness.")
        print("   Use Neo-CLI for command-line deployment:")
        print("   ./neo-cli --network testnet")
        print(f"   import key {MASTER_WIF}")
        print("   deploy src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    else:
        print("\n❌ Deployment validation failed")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print(f"\n🎯 READY FOR DEPLOYMENT!")
            print(f"   Your contract is validated and ready to deploy.")
        else:
            print(f"\n❌ Deployment preparation failed")
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")