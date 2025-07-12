#!/usr/bin/env python3
"""
Neo N3 Transaction Builder for Contract Deployment
Based on Neo.Network.RpcClient and Neo.CLI implementation patterns
"""

import json
import base64
import hashlib
import struct
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# Neo N3 Constants (from Neo source)
MANAGEMENT_CONTRACT = bytes.fromhex("fffdc93764dbaddd97c48f252a53ea4643faa3fd")[::-1]  # Reverse for little-endian
GAS_TOKEN = bytes.fromhex("d2a4cff31913016155e38e474a2c06d08be276cf")[::-1]
NEO_TOKEN = bytes.fromhex("ef4073a0f2b305a38ec4050e4d3d28bc40ea63f5")[::-1]

# OpCodes (from Neo VM)
class OpCode:
    PUSHDATA1 = 0x0C
    PUSHDATA2 = 0x0D
    PUSH2 = 0x52
    PACK = 0xC1
    SYSCALL = 0x41
    PUSH0 = 0x10
    PUSHINT8 = 0x00
    PUSHINT16 = 0x01
    PUSHINT32 = 0x02

# InteropService IDs (from Neo)
SYSTEM_CONTRACT_CALL = 0x627D5B52  # System.Contract.Call

class Neo3ScriptBuilder:
    """Build Neo N3 VM scripts following official patterns"""
    
    def __init__(self):
        self.script = bytearray()
    
    def emit_opcode(self, opcode: int):
        """Emit an opcode"""
        self.script.append(opcode)
    
    def emit_bytes(self, data: bytes):
        """Emit raw bytes"""
        self.script.extend(data)
    
    def emit_push_data(self, data: bytes):
        """Emit PUSHDATA with proper size encoding for Neo N3"""
        length = len(data)
        
        if length <= 75:
            self.script.append(length)
        elif length <= 255:
            self.emit_opcode(OpCode.PUSHDATA1)
            self.script.append(length)
        elif length <= 65535:
            self.emit_opcode(OpCode.PUSHDATA2)
            self.script.extend(struct.pack('<H', length))
        elif length <= 4294967295:  # Support larger data for NEF files
            self.emit_opcode(0x0E)  # PUSHDATA4
            self.script.extend(struct.pack('<I', length))
        else:
            raise ValueError(f"Data too large: {length} bytes")
        
        self.script.extend(data)
    
    def emit_push_string(self, text: str):
        """Push string data"""
        data = text.encode('utf-8')
        self.emit_push_data(data)
    
    def emit_push_int(self, value: int):
        """Push integer value"""
        if value == 0:
            self.emit_opcode(OpCode.PUSH0)
        elif 1 <= value <= 16:
            self.emit_opcode(0x50 + value)  # PUSH1-PUSH16
        elif -128 <= value <= 127:
            self.emit_opcode(OpCode.PUSHINT8)
            self.script.append(value & 0xFF)
        elif -32768 <= value <= 32767:
            self.emit_opcode(OpCode.PUSHINT16)
            self.script.extend(struct.pack('<h', value))
        else:
            self.emit_opcode(OpCode.PUSHINT32)
            self.script.extend(struct.pack('<i', value))
    
    def emit_syscall(self, syscall_id: int):
        """Emit syscall"""
        self.emit_opcode(OpCode.SYSCALL)
        self.script.extend(struct.pack('<I', syscall_id))
    
    def to_bytes(self) -> bytes:
        """Get final script bytes"""
        return bytes(self.script)

class Neo3DeploymentTransaction:
    """Create deployment transaction following Neo.CLI patterns"""
    
    @staticmethod
    def create_deploy_script(nef_file: Path, manifest_file: Path) -> bytes:
        """
        Create deployment script following Neo.CLI MainService.Contracts.cs
        Equivalent to: ContractManagement.Deploy(nefFile, manifest)
        """
        try:
            # Read NEF file
            with open(nef_file, 'rb') as f:
                nef_data = f.read()
            
            # Read manifest
            with open(manifest_file, 'r') as f:
                manifest_data = f.read()
            
            print(f"📁 Creating deploy script:")
            print(f"   NEF size: {len(nef_data)} bytes")
            print(f"   Manifest size: {len(manifest_data)} bytes")
            
            # Validate NEF file
            if not nef_data.startswith(b'NEF3'):
                raise ValueError("Invalid NEF file format")
            
            # Build script following Neo VM stack operations
            builder = Neo3ScriptBuilder()
            
            # Push parameters in reverse order (Neo VM is stack-based)
            # 1. Push manifest (string parameter)
            builder.emit_push_string(manifest_data)
            
            # 2. Push NEF data (byte array parameter)
            builder.emit_push_data(nef_data)
            
            # 3. Push parameter count (2 parameters)
            builder.emit_push_int(2)
            
            # 4. Pack parameters into array
            builder.emit_opcode(OpCode.PACK)
            
            # 5. Push method name "deploy"
            builder.emit_push_string("deploy")
            
            # 6. Push contract hash (ContractManagement)
            builder.emit_push_data(MANAGEMENT_CONTRACT)
            
            # 7. Call System.Contract.Call
            builder.emit_syscall(SYSTEM_CONTRACT_CALL)
            
            script = builder.to_bytes()
            
            print(f"✅ Deploy script created: {len(script)} bytes")
            
            return script
            
        except Exception as e:
            print(f"❌ Error creating deploy script: {e}")
            raise
    
    @staticmethod
    def calculate_hash(script: bytes) -> str:
        """Calculate script hash"""
        hash_data = hashlib.sha256(script).digest()
        return "0x" + hash_data[::-1].hex()  # Reverse for little-endian display

class Neo3TransactionValidator:
    """Validate transaction before deployment"""
    
    def __init__(self, rpc_endpoint: str):
        self.rpc_endpoint = rpc_endpoint
    
    def validate_deploy_script(self, script: bytes) -> Dict[str, Any]:
        """Validate deploy script via RPC invokescript"""
        import requests
        
        script_b64 = base64.b64encode(script).decode()
        
        payload = {
            "jsonrpc": "2.0",
            "method": "invokescript",
            "params": [script_b64],
            "id": 1
        }
        
        try:
            response = requests.post(self.rpc_endpoint, json=payload, timeout=30)
            result = response.json()
            
            if "error" in result:
                print(f"❌ Script validation error: {result['error']}")
                return {"valid": False, "error": result['error']}
            
            invoke_result = result.get("result", {})
            state = invoke_result.get("state", "FAULT")
            
            if state == "HALT":
                gas_consumed = int(invoke_result.get("gasconsumed", "0"))
                print(f"✅ Script validation successful")
                print(f"   Gas consumed: {gas_consumed / 100_000_000} GAS")
                
                # Extract contract hash from stack if available
                contract_hash = None
                stack = invoke_result.get("stack", [])
                if stack and len(stack) > 0:
                    stack_item = stack[0]
                    if stack_item.get("type") == "InteropInterface":
                        # Contract deployment successful
                        print("✅ Contract deployment would succeed")
                
                return {
                    "valid": True,
                    "gas_consumed": gas_consumed,
                    "state": state,
                    "stack": stack
                }
            else:
                exception = invoke_result.get("exception", "Unknown error")
                print(f"❌ Script validation failed: {exception}")
                return {"valid": False, "error": exception}
                
        except Exception as e:
            print(f"❌ Network error during validation: {e}")
            return {"valid": False, "error": str(e)}

def test_deployment_script():
    """Test the deployment script creation and validation"""
    print("🧪 Testing Neo N3 Deployment Script Creation")
    print("=" * 55)
    
    # File paths
    nef_file = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
    manifest_file = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
    
    # Check files exist
    if not nef_file.exists():
        print(f"❌ NEF file not found: {nef_file}")
        return False
    
    if not manifest_file.exists():
        print(f"❌ Manifest file not found: {manifest_file}")
        return False
    
    try:
        # Create deployment script
        print("\n🔨 Creating deployment script...")
        script = Neo3DeploymentTransaction.create_deploy_script(nef_file, manifest_file)
        
        # Calculate script hash
        script_hash = Neo3DeploymentTransaction.calculate_hash(script)
        print(f"📊 Script hash: {script_hash}")
        
        # Validate script via RPC
        print("\n🔍 Validating script via TestNet RPC...")
        validator = Neo3TransactionValidator("http://seed1t5.neo.org:20332")
        validation_result = validator.validate_deploy_script(script)
        
        if validation_result["valid"]:
            print("\n✅ DEPLOYMENT SCRIPT VALIDATION SUCCESSFUL!")
            print(f"   Script size: {len(script)} bytes")
            print(f"   Estimated gas: {validation_result['gas_consumed'] / 100_000_000} GAS")
            print("\n📝 NEXT STEPS:")
            print("   1. This script validates your contract can be deployed")
            print("   2. For actual deployment, use NeoLine or Neo-CLI:")
            print("      - NeoLine: https://neoline.io/")
            print("      - Neo-CLI: Download and run with TestNet")
            print("   3. The deployment will create a contract with predictable behavior")
            
            return True
        else:
            print(f"\n❌ Script validation failed: {validation_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing deployment: {e}")
        return False

if __name__ == "__main__":
    try:
        success = test_deployment_script()
        if success:
            print(f"\n🎯 Your Neo N3 contract is ready for deployment!")
            print(f"   All validation checks passed.")
        else:
            print(f"\n❌ Deployment validation failed")
    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")