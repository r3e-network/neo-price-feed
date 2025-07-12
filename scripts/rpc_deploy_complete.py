#!/usr/bin/env python3
"""
Complete Neo N3 RPC deployment with transaction construction and signing
Based on Neo.Network.RpcClient and Neo.Cryptography patterns
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
import ecdsa
from ecdsa.curves import SECP256R1
from ecdsa.keys import SigningKey
import io

# Neo N3 Constants
TESTNET_RPC = "http://seed1t5.neo.org:20332"
MASTER_WIF = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb"
MASTER_ADDRESS = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"

# Contract hashes (little-endian)
MANAGEMENT_CONTRACT = bytes.fromhex("fffdc93764dbaddd97c48f252a53ea4643faa3fd")[::-1]
GAS_TOKEN = bytes.fromhex("d2a4cff31913016155e38e474a2c06d08be276cf")[::-1]

# Neo N3 VM OpCodes
class OpCode:
    PUSHDATA1 = 0x0C
    PUSHDATA2 = 0x0D  
    PUSHDATA4 = 0x0E
    PUSH2 = 0x52
    PACK = 0xC1
    SYSCALL = 0x41
    RET = 0x40

# Syscalls
SYSTEM_CONTRACT_CALL = 0x627D5B52

def wif_to_private_key(wif: str) -> bytes:
    """Convert WIF to private key bytes"""
    # Base58 decode
    decoded = base58_decode(wif)
    
    # Remove prefix (0x80) and suffix (0x01 for compressed)
    if len(decoded) == 37 and decoded[0] == 0x80 and decoded[-4] == 0x01:
        private_key = decoded[1:33]
    elif len(decoded) == 33 and decoded[0] == 0x80:
        private_key = decoded[1:33]
    else:
        raise ValueError("Invalid WIF format")
    
    return private_key

def base58_decode(s: str) -> bytes:
    """Base58 decode"""
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    base_count = len(alphabet)
    decoded = 0
    multi = 1
    
    for char in reversed(s):
        decoded += multi * alphabet.index(char)
        multi *= base_count
    
    h = hex(decoded)[2:]
    if len(h) % 2:
        h = '0' + h
    
    result = bytes.fromhex(h)
    
    # Handle leading zeros
    pad = 0
    for c in s:
        if c == alphabet[0]:
            pad += 1
        else:
            break
    
    return bytes([0] * pad) + result

def address_to_script_hash(address: str) -> bytes:
    """Convert Neo address to script hash"""
    decoded = base58_decode(address)
    # Remove version byte and checksum
    return decoded[1:21]

class Neo3Transaction:
    """Neo N3 Transaction class"""
    
    def __init__(self):
        self.version = 0
        self.nonce = int(time.time()) & 0xFFFFFFFF
        self.system_fee = 0
        self.network_fee = 0
        self.valid_until_block = 0
        self.signers = []
        self.attributes = []
        self.script = b''
        self.witnesses = []
    
    def serialize_unsigned(self) -> bytes:
        """Serialize transaction without witnesses"""
        stream = io.BytesIO()
        
        # Version
        stream.write(struct.pack('<B', self.version))
        
        # Nonce
        stream.write(struct.pack('<I', self.nonce))
        
        # System fee
        stream.write(self._serialize_varint(self.system_fee))
        
        # Network fee  
        stream.write(self._serialize_varint(self.network_fee))
        
        # Valid until block
        stream.write(struct.pack('<I', self.valid_until_block))
        
        # Signers
        stream.write(struct.pack('<B', len(self.signers)))
        for signer in self.signers:
            stream.write(signer)
        
        # Attributes
        stream.write(struct.pack('<B', len(self.attributes)))
        for attr in self.attributes:
            stream.write(attr)
        
        # Script
        stream.write(self._serialize_var_bytes(self.script))
        
        return stream.getvalue()
    
    def serialize_with_witnesses(self) -> bytes:
        """Serialize complete transaction with witnesses"""
        unsigned = self.serialize_unsigned()
        
        stream = io.BytesIO()
        stream.write(unsigned)
        
        # Witnesses
        stream.write(struct.pack('<B', len(self.witnesses)))
        for witness in self.witnesses:
            stream.write(witness)
        
        return stream.getvalue()
    
    def _serialize_varint(self, value: int) -> bytes:
        """Serialize variable-length integer"""
        if value < 0xFD:
            return struct.pack('<B', value)
        elif value <= 0xFFFF:
            return struct.pack('<BH', 0xFD, value)
        elif value <= 0xFFFFFFFF:
            return struct.pack('<BI', 0xFE, value)
        else:
            return struct.pack('<BQ', 0xFF, value)
    
    def _serialize_var_bytes(self, data: bytes) -> bytes:
        """Serialize variable-length byte array"""
        return self._serialize_varint(len(data)) + data

class Neo3Deployer:
    """Complete Neo N3 deployment via RPC"""
    
    def __init__(self):
        self.rpc_endpoint = TESTNET_RPC
        self.private_key = wif_to_private_key(MASTER_WIF)
        self.script_hash = address_to_script_hash(MASTER_ADDRESS)
    
    def rpc_call(self, method: str, params: List = None) -> Optional[Dict[str, Any]]:
        """Make RPC call"""
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
    
    def get_current_block_height(self) -> int:
        """Get current block height"""
        result = self.rpc_call("getblockcount")
        return result if result else 0
    
    def create_deployment_script(self, nef_file: Path, manifest_file: Path) -> bytes:
        """Create deployment script"""
        with open(nef_file, 'rb') as f:
            nef_data = f.read()
        
        with open(manifest_file, 'r') as f:
            manifest_data = f.read()
        
        print(f"📁 Creating deployment script:")
        print(f"   NEF size: {len(nef_data)} bytes")
        print(f"   Manifest size: {len(manifest_data)} bytes")
        
        # Build deployment script
        script = io.BytesIO()
        
        # Push manifest (string)
        manifest_bytes = manifest_data.encode('utf-8')
        self._emit_push_data(script, manifest_bytes)
        
        # Push NEF data (byte array)
        self._emit_push_data(script, nef_data)
        
        # Push parameter count (2)
        script.write(bytes([OpCode.PUSH2]))
        
        # Pack parameters
        script.write(bytes([OpCode.PACK]))
        
        # Push method name "deploy"
        deploy_bytes = b"deploy"
        self._emit_push_data(script, deploy_bytes)
        
        # Push contract hash (Management contract)
        self._emit_push_data(script, MANAGEMENT_CONTRACT)
        
        # System.Contract.Call
        script.write(bytes([OpCode.SYSCALL]))
        script.write(struct.pack('<I', SYSTEM_CONTRACT_CALL))
        
        return script.getvalue()
    
    def _emit_push_data(self, stream: io.BytesIO, data: bytes):
        """Emit PUSHDATA instruction"""
        length = len(data)
        
        if length <= 75:
            stream.write(bytes([length]))
        elif length <= 255:
            stream.write(bytes([OpCode.PUSHDATA1, length]))
        elif length <= 65535:
            stream.write(bytes([OpCode.PUSHDATA2]))
            stream.write(struct.pack('<H', length))
        else:
            stream.write(bytes([OpCode.PUSHDATA4]))
            stream.write(struct.pack('<I', length))
        
        stream.write(data)
    
    def estimate_fees(self, script: bytes) -> Dict[str, int]:
        """Estimate deployment fees"""
        # Test invoke to get system fee
        script_b64 = base64.b64encode(script).decode()
        
        result = self.rpc_call("invokescript", [script_b64])
        if result and result.get("state") == "HALT":
            system_fee = int(result.get("gasconsumed", "0"))
        else:
            # Conservative estimate
            system_fee = 10_000_000_000  # 10 GAS
        
        # Estimate network fee (conservative)
        tx_size = len(script) + 200  # Script + transaction overhead
        network_fee = tx_size * 1000  # 1000 datoshi per byte
        
        return {
            "system_fee": system_fee,
            "network_fee": network_fee,
            "total": system_fee + network_fee
        }
    
    def create_witness(self, message: bytes) -> bytes:
        """Create transaction witness (signature)"""
        # Sign message with private key
        signing_key = SigningKey.from_string(self.private_key, curve=SECP256R1, hashfunc=hashlib.sha256)
        signature = signing_key.sign_digest(hashlib.sha256(message).digest())
        
        # DER encode signature
        r = signature[:32]
        s = signature[32:]
        
        # Create signature script
        sig_script = io.BytesIO()
        
        # Push signature
        sig_data = b'\x0c\x40' + signature  # PUSHDATA1 64 + signature
        sig_script.write(sig_data)
        
        # Create verification script (CheckWitness with script hash)
        verify_script = io.BytesIO()
        verify_script.write(b'\x0c\x14')  # PUSHDATA1 20
        verify_script.write(self.script_hash)
        verify_script.write(b'\x41\x9e\xd0\xdc\x3a')  # SYSCALL System.Runtime.CheckWitness
        
        # Combine into witness
        witness = io.BytesIO()
        
        # Invocation script
        inv_script = sig_script.getvalue()
        witness.write(struct.pack('<B', len(inv_script)))
        witness.write(inv_script)
        
        # Verification script  
        ver_script = verify_script.getvalue()
        witness.write(struct.pack('<B', len(ver_script)))
        witness.write(ver_script)
        
        return witness.getvalue()
    
    def deploy_contract(self, nef_file: Path, manifest_file: Path) -> Optional[str]:
        """Deploy contract via RPC"""
        print("🚀 Starting Neo N3 Contract Deployment via RPC")
        print("=" * 55)
        
        # Get current block height
        current_height = self.get_current_block_height()
        if not current_height:
            print("❌ Could not get current block height")
            return None
        
        print(f"✅ Current block height: {current_height}")
        
        # Create deployment script
        try:
            script = self.create_deployment_script(nef_file, manifest_file)
            print(f"✅ Deployment script created: {len(script)} bytes")
        except Exception as e:
            print(f"❌ Error creating deployment script: {e}")
            return None
        
        # Estimate fees
        fees = self.estimate_fees(script)
        print(f"💰 Estimated fees:")
        print(f"   System fee: {fees['system_fee'] / 100_000_000} GAS")
        print(f"   Network fee: {fees['network_fee'] / 100_000_000} GAS")
        print(f"   Total: {fees['total'] / 100_000_000} GAS")
        
        # Create transaction
        tx = Neo3Transaction()
        tx.script = script
        tx.system_fee = fees['system_fee']
        tx.network_fee = fees['network_fee']
        tx.valid_until_block = current_height + 1000
        
        # Add signer
        signer = io.BytesIO()
        signer.write(self.script_hash)  # Account script hash
        signer.write(bytes([0]))  # Scope: None
        tx.signers = [signer.getvalue()]
        
        # Serialize unsigned transaction
        unsigned_tx = tx.serialize_unsigned()
        print(f"✅ Transaction created: {len(unsigned_tx)} bytes")
        
        # Create witness
        try:
            witness = self.create_witness(unsigned_tx)
            tx.witnesses = [witness]
            print(f"✅ Transaction signed")
        except Exception as e:
            print(f"❌ Error signing transaction: {e}")
            return None
        
        # Serialize final transaction
        final_tx = tx.serialize_with_witnesses()
        tx_hex = final_tx.hex()
        
        print(f"📤 Sending transaction to network...")
        print(f"   Transaction hex: {tx_hex[:100]}...")
        
        # Send transaction
        result = self.rpc_call("sendrawtransaction", [tx_hex])
        
        if result:
            if isinstance(result, dict) and "hash" in result:
                tx_hash = result["hash"]
            else:
                tx_hash = str(result)
            
            print(f"✅ Transaction sent successfully!")
            print(f"   Transaction hash: {tx_hash}")
            
            return tx_hash
        else:
            print(f"❌ Failed to send transaction")
            return None

def main():
    """Main deployment function"""
    print("🎯 Neo N3 RPC Contract Deployment")
    print("=" * 40)
    
    # Check files
    nef_file = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef") 
    manifest_file = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
    
    if not nef_file.exists():
        print(f"❌ NEF file not found: {nef_file}")
        return False
    
    if not manifest_file.exists():
        print(f"❌ Manifest file not found: {manifest_file}")
        return False
    
    # Deploy contract
    deployer = Neo3Deployer()
    
    try:
        tx_hash = deployer.deploy_contract(nef_file, manifest_file)
        
        if tx_hash:
            print(f"\n🎉 DEPLOYMENT SUCCESSFUL!")
            print(f"   Transaction: {tx_hash}")
            print(f"   Explorer: https://testnet.explorer.onegate.space/transaction/{tx_hash}")
            print(f"\n📝 Next steps:")
            print(f"   1. Wait for transaction confirmation (~15 seconds)")
            print(f"   2. Extract contract hash from transaction")
            print(f"   3. Update configuration: python3 scripts/update-contract-hash.py CONTRACT_HASH")
            print(f"   4. Initialize contract: python3 scripts/initialize-contract.py")
            return True
        else:
            print(f"\n❌ Deployment failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Deployment error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print(f"\n💡 Alternative: Use NeoLine extension for easier deployment")
            print(f"   https://neoline.io/")
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()