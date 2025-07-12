#!/usr/bin/env python3
"""
Simplified Neo N3 RPC deployment using built-in libraries only
Demonstrates proper transaction construction for deployment
"""

import json
import requests
import base64
import hashlib
import struct
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import binascii

# Neo N3 Constants
TESTNET_RPC = "http://seed1t5.neo.org:20332"
MASTER_WIF = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb"
MASTER_ADDRESS = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"

# Contract hashes (little-endian format)
MANAGEMENT_CONTRACT = "fda3fa4346ea532a258fc497ddaddb6437c9fdff"
GAS_TOKEN = "cf76d2be086d4d5e3e474a2c06d08be276cf"

class Neo3RpcDeployer:
    """Simplified Neo N3 deployment via RPC calls"""
    
    def __init__(self):
        self.rpc_endpoint = TESTNET_RPC
    
    def rpc_call(self, method: str, params: List = None) -> Optional[Dict[str, Any]]:
        """Make RPC call to Neo N3 node"""
        payload = {
            "jsonrpc": "2.0",
            "method": method, 
            "params": params or [],
            "id": 1
        }
        
        try:
            response = requests.post(self.rpc_endpoint, json=payload, timeout=30)
            result = response.json()
            
            if "error" in result:
                print(f"❌ RPC Error: {result['error']}")
                return None
            
            return result.get("result")
        except Exception as e:
            print(f"❌ Network error: {e}")
            return None
    
    def validate_deployment_environment(self) -> bool:
        """Validate deployment environment"""
        print("🔍 Validating deployment environment...")
        
        # Check TestNet connectivity
        block_count = self.rpc_call("getblockcount")
        if not block_count:
            print("❌ Cannot connect to TestNet")
            return False
        
        print(f"✅ TestNet connected (Block {block_count})")
        
        # Check account balance
        balance_result = self.rpc_call("getnep17balances", [MASTER_ADDRESS])
        if not balance_result:
            print("❌ Cannot get account balance")
            return False
        
        gas_balance = 0
        for balance in balance_result.get("balance", []):
            if balance["assethash"] == "0xd2a4cff31913016155e38e474a2c06d08be276cf":
                gas_balance = int(balance["amount"]) / 100_000_000
        
        print(f"✅ Account balance: {gas_balance} GAS")
        
        if gas_balance < 15:
            print("❌ Insufficient GAS for deployment")
            return False
        
        return True
    
    def create_deployment_script_hex(self, nef_file: Path, manifest_file: Path) -> Optional[str]:
        """Create deployment script and return as hex string"""
        try:
            # Read contract files
            with open(nef_file, 'rb') as f:
                nef_data = f.read()
            
            with open(manifest_file, 'r') as f:
                manifest_data = f.read()
            
            print(f"📁 Contract files loaded:")
            print(f"   NEF: {len(nef_data)} bytes")
            print(f"   Manifest: {len(manifest_data)} bytes")
            
            # Validate NEF format
            if not nef_data.startswith(b'NEF3'):
                print("❌ Invalid NEF file format")
                return None
            
            # Validate manifest JSON
            try:
                manifest_obj = json.loads(manifest_data)
                if "name" not in manifest_obj:
                    print("❌ Invalid manifest format")
                    return None
            except:
                print("❌ Invalid manifest JSON")
                return None
            
            # Create deployment script using Neo N3 VM opcodes
            script_parts = []
            
            # Push manifest (as string parameter)
            manifest_bytes = manifest_data.encode('utf-8')
            script_parts.append(self._create_push_data_opcode(manifest_bytes))
            
            # Push NEF data (as byte array parameter)  
            script_parts.append(self._create_push_data_opcode(nef_data))
            
            # Push parameter count (2 parameters)
            script_parts.append("52")  # PUSH2
            
            # Pack parameters into array
            script_parts.append("c1")  # PACK
            
            # Push method name "deploy"
            deploy_bytes = b"deploy"
            script_parts.append(self._create_push_data_opcode(deploy_bytes))
            
            # Push management contract hash
            mgmt_hash = bytes.fromhex(MANAGEMENT_CONTRACT)[::-1]  # Reverse for little-endian
            script_parts.append(self._create_push_data_opcode(mgmt_hash))
            
            # Call System.Contract.Call
            script_parts.append("41")  # SYSCALL
            script_parts.append("525bd627")  # System.Contract.Call ID (little-endian)
            
            # Combine all parts
            script_hex = "".join(script_parts)
            
            print(f"✅ Deployment script created: {len(script_hex)//2} bytes")
            
            return script_hex
            
        except Exception as e:
            print(f"❌ Error creating deployment script: {e}")
            return None
    
    def _create_push_data_opcode(self, data: bytes) -> str:
        """Create PUSHDATA opcode for given data"""
        length = len(data)
        
        if length <= 75:
            # Direct push
            return f"{length:02x}{data.hex()}"
        elif length <= 255:
            # PUSHDATA1
            return f"0c{length:02x}{data.hex()}"
        elif length <= 65535:
            # PUSHDATA2 (little-endian length)
            return f"0d{struct.pack('<H', length).hex()}{data.hex()}"
        else:
            # PUSHDATA4 (little-endian length)
            return f"0e{struct.pack('<I', length).hex()}{data.hex()}"
    
    def test_deployment_script(self, script_hex: str) -> Dict[str, Any]:
        """Test deployment script via invokescript"""
        print("🧪 Testing deployment script...")
        
        # Convert hex to base64 for RPC
        script_bytes = bytes.fromhex(script_hex)
        script_b64 = base64.b64encode(script_bytes).decode()
        
        # Test invoke
        result = self.rpc_call("invokescript", [script_b64])
        
        if result:
            state = result.get("state", "FAULT")
            gas_consumed = int(result.get("gasconsumed", "0"))
            
            if state == "HALT":
                print(f"✅ Script test successful")
                print(f"   Gas consumed: {gas_consumed / 100_000_000} GAS")
                print(f"   State: {state}")
                
                return {
                    "success": True,
                    "gas_consumed": gas_consumed,
                    "state": state
                }
            else:
                exception = result.get("exception", "Unknown error")
                print(f"❌ Script test failed: {exception}")
                print(f"   State: {state}")
                
                return {
                    "success": False,
                    "error": exception,
                    "state": state
                }
        else:
            print("❌ Could not test script")
            return {"success": False, "error": "RPC call failed"}
    
    def demonstrate_deployment_process(self, nef_file: Path, manifest_file: Path) -> bool:
        """Demonstrate the complete deployment process"""
        print("🚀 Neo N3 Contract Deployment via RPC")
        print("=" * 45)
        
        # Validate environment
        if not self.validate_deployment_environment():
            return False
        
        # Create deployment script
        script_hex = self.create_deployment_script_hex(nef_file, manifest_file)
        if not script_hex:
            return False
        
        # Test deployment script
        test_result = self.test_deployment_script(script_hex)
        
        if test_result["success"]:
            print(f"\n✅ DEPLOYMENT VALIDATION SUCCESSFUL!")
            print(f"   Your contract is ready for deployment")
            print(f"   Estimated cost: {test_result['gas_consumed'] / 100_000_000} GAS")
            
            print(f"\n📋 DEPLOYMENT SCRIPT ANALYSIS:")
            print(f"   Script size: {len(script_hex)//2} bytes")
            print(f"   Script hex: {script_hex[:100]}...")
            
            print(f"\n⚠️  IMPORTANT NOTES:")
            print(f"   1. This demonstrates proper script construction")
            print(f"   2. Actual deployment requires transaction signing")
            print(f"   3. For immediate deployment, use NeoLine or Neo-CLI:")
            print(f"      - NeoLine: https://neoline.io/")
            print(f"      - Neo-CLI: Download from Neo releases")
            
            print(f"\n🎯 YOUR DEPLOYMENT IS VALIDATED AND READY!")
            
            return True
        else:
            print(f"\n❌ Deployment validation failed: {test_result.get('error', 'Unknown error')}")
            return False

def main():
    """Main deployment demonstration"""
    print("🎯 Neo N3 RPC Deployment Demonstration")
    print("=" * 45)
    
    # Check contract files
    nef_file = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    manifest_file = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
    
    if not nef_file.exists():
        print(f"❌ NEF file not found: {nef_file}")
        return False
    
    if not manifest_file.exists():
        print(f"❌ Manifest file not found: {manifest_file}")
        return False
    
    # Run deployment demonstration
    deployer = Neo3RpcDeployer()
    
    try:
        success = deployer.demonstrate_deployment_process(nef_file, manifest_file)
        
        if success:
            print(f"\n🎉 DEPLOYMENT DEMONSTRATION COMPLETE!")
            print(f"   Your Neo N3 Price Feed Oracle is validated and ready!")
            
            print(f"\n📝 RECOMMENDED NEXT STEPS:")
            print(f"   1. Use NeoLine extension for actual deployment:")
            print(f"      - Install: https://neoline.io/")
            print(f"      - Import key: {MASTER_WIF}")
            print(f"      - Deploy contract files")
            print(f"   2. Or use Neo-CLI for command-line deployment")
            print(f"   3. Update configuration with contract hash")
            print(f"   4. Initialize and test your oracle")
            
            return True
        else:
            print(f"\n❌ Deployment validation failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during deployment demonstration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment demonstration cancelled")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")