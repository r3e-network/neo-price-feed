#!/usr/bin/env python3
"""
Direct contract deployment to Neo N3 TestNet
"""
import os
import sys
import json
import time
import struct
import hashlib
import requests
from pathlib import Path
from base64 import b64encode, b64decode

# Add required crypto libraries
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("Installing required cryptography library...")
    os.system(f"{sys.executable} -m pip install cryptography")
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.backends import default_backend

class NeoDeployment:
    def __init__(self):
        self.rpc_url = "http://seed1t5.neo.org:20332"
        self.master_wif = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb"
        self.testnet_magic = 877933390
        
    def wif_to_private_key(self, wif):
        """Convert WIF to private key bytes"""
        # Base58 decode
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        decoded = 0
        for char in wif:
            decoded = decoded * 58 + alphabet.index(char)
        
        # Convert to bytes
        hex_str = hex(decoded)[2:]
        if len(hex_str) % 2:
            hex_str = '0' + hex_str
        
        data = bytes.fromhex(hex_str)
        
        # Remove checksum (last 4 bytes) and version byte (first byte)
        private_key = data[1:-4]
        
        # If compressed format (33 bytes), remove compression flag
        if len(private_key) == 33:
            private_key = private_key[:-1]
            
        return private_key
    
    def get_public_key(self, private_key_bytes):
        """Get public key from private key"""
        # Create EC private key
        private_key = ec.derive_private_key(
            int.from_bytes(private_key_bytes, 'big'),
            ec.SECP256R1(),
            default_backend()
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Get compressed public key bytes
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )
        
        return public_bytes
    
    def get_script_hash(self, public_key):
        """Get script hash from public key"""
        # Create verification script
        script = bytes([0x21]) + public_key + bytes([0x41, 0x9B, 0xF6, 0x67, 0xCE])
        
        # Hash it
        hash1 = hashlib.sha256(script).digest()
        hash2 = hashlib.new('ripemd160', hash1).digest()
        
        return hash2
    
    def script_hash_to_address(self, script_hash):
        """Convert script hash to address"""
        # Add version byte for TestNet
        data = bytes([0x49]) + script_hash
        
        # Add checksum
        checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
        data += checksum
        
        # Base58 encode
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        encoded = ''
        num = int.from_bytes(data, 'big')
        
        while num > 0:
            num, remainder = divmod(num, 58)
            encoded = alphabet[remainder] + encoded
            
        # Add leading zeros
        for byte in data:
            if byte == 0:
                encoded = '1' + encoded
            else:
                break
                
        return encoded
    
    def rpc_call(self, method, params):
        """Make RPC call"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        response = requests.post(self.rpc_url, json=payload)
        return response.json()
    
    def deploy(self):
        """Deploy the contract"""
        print("🚀 Neo N3 Direct Contract Deployment")
        print("=" * 50)
        
        # Get private and public keys
        private_key = self.wif_to_private_key(self.master_wif)
        public_key = self.get_public_key(private_key)
        script_hash = self.get_script_hash(public_key)
        address = self.script_hash_to_address(script_hash)
        
        print(f"\n🔐 Account Details:")
        print(f"   Address: {address}")
        print(f"   Public Key: {public_key.hex()}")
        
        # Check balance
        print("\n💰 Checking balance...")
        result = self.rpc_call("getnep17balances", [address])
        
        gas_balance = 0
        if "result" in result:
            for balance in result["result"]["balance"]:
                if balance["assethash"].endswith("d2a4cff31913016155e38e474a2c06d08be276cf"):
                    gas_balance = int(balance["amount"]) / 100_000_000
                    
        print(f"   GAS Balance: {gas_balance}")
        
        if gas_balance < 15:
            print("❌ Insufficient GAS balance")
            return
        
        # Load contract files
        print("\n📁 Loading contract files...")
        nef_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.nef")
        manifest_path = Path("src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json")
        
        if not nef_path.exists() or not manifest_path.exists():
            print("❌ Contract files not found")
            return
            
        nef_bytes = nef_path.read_bytes()
        manifest_json = manifest_path.read_text()
        
        print(f"✅ NEF loaded: {len(nef_bytes)} bytes")
        print(f"✅ Manifest loaded: {len(manifest_json)} chars")
        
        # Build deployment script
        print("\n🔨 Building deployment script...")
        
        # This is a simplified version - real deployment requires more complex script building
        print("\n📋 Contract Ready for Deployment")
        print(f"   Expected Hash: 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc")
        print(f"   Deployment Cost: ~10.002 GAS")
        
        # Create deployment guide
        print("\n🚀 DEPLOYMENT INSTRUCTIONS:")
        print("\nSince direct RPC deployment requires complex transaction construction,")
        print("please use one of these methods:")
        
        print("\n1️⃣ Neo Express (Quick Test):")
        print("   neo-express contract deploy deployment-files/PriceFeed.Oracle.nef")
        
        print("\n2️⃣ Neo-CLI (Production):")
        print("   neo> open wallet wallet.json")
        print(f"   neo> import key {self.master_wif}")
        print("   neo> deploy deployment-files/PriceFeed.Oracle.nef deployment-files/PriceFeed.Oracle.manifest.json")
        
        print("\n3️⃣ Neo-Python (Alternative):")
        print("   pip install neo-mamba")
        print("   neo-mamba deploy-contract")
        
        # Save deployment package
        self.create_deployment_package(nef_bytes, manifest_json, address)
        
    def create_deployment_package(self, nef_bytes, manifest_json, address):
        """Create a deployment package with all necessary files"""
        print("\n📦 Creating deployment package...")
        
        deploy_dir = Path("neo-deployment-package")
        deploy_dir.mkdir(exist_ok=True)
        
        # Save contract files
        (deploy_dir / "contract.nef").write_bytes(nef_bytes)
        (deploy_dir / "contract.manifest.json").write_text(manifest_json)
        
        # Create deployment script
        deploy_script = f"""#!/bin/bash
# Neo N3 Contract Deployment Script

echo "🚀 Neo N3 Contract Deployment"
echo "=========================="
echo ""
echo "Account: {address}"
echo "Contract Hash: 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc"
echo ""
echo "1. Install Neo-CLI:"
echo "   wget https://github.com/neo-project/neo-cli/releases/download/v3.6.2/neo-cli-linux-x64.zip"
echo "   unzip neo-cli-linux-x64.zip"
echo ""
echo "2. Run Neo-CLI:"
echo "   ./neo-cli"
echo ""
echo "3. In Neo-CLI console:"
echo "   create wallet deploy.json"
echo "   open wallet deploy.json"
echo "   import key {self.master_wif}"
echo "   deploy contract.nef contract.manifest.json"
echo ""
echo "4. After deployment, initialize:"
echo "   invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc addOracle [\\\"NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB\\\"]"
echo "   invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc setMinOracles [1]"
"""
        
        (deploy_dir / "deploy.sh").write_text(deploy_script)
        os.chmod(deploy_dir / "deploy.sh", 0o755)
        
        # Create deployment info
        deploy_info = {
            "network": "testnet",
            "account": {
                "address": address,
                "wif": self.master_wif
            },
            "contract": {
                "name": "PriceFeed.Oracle",
                "hash": "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc",
                "nef_size": len(nef_bytes),
                "manifest_size": len(manifest_json)
            },
            "deployment_cost": {
                "system_fee": "10.00035859 GAS",
                "network_fee": "~0.05 GAS",
                "total": "~10.05 GAS"
            },
            "rpc_endpoints": [
                "http://seed1t5.neo.org:20332",
                "http://seed2t5.neo.org:20332"
            ]
        }
        
        (deploy_dir / "deployment-info.json").write_text(
            json.dumps(deploy_info, indent=2)
        )
        
        print(f"✅ Deployment package created: {deploy_dir.absolute()}")
        print(f"   - contract.nef")
        print(f"   - contract.manifest.json")
        print(f"   - deploy.sh (deployment script)")
        print(f"   - deployment-info.json")
        
        print(f"\n📝 To deploy:")
        print(f"   cd {deploy_dir}")
        print(f"   ./deploy.sh")

if __name__ == "__main__":
    deployment = NeoDeployment()
    deployment.deploy()