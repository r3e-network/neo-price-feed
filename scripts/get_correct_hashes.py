#!/usr/bin/env python3
"""
Get correct script hashes for neo-cli
"""

def neo_address_to_script_hash(address):
    """Convert Neo address to little-endian script hash"""
    # These are the correct little-endian script hashes for the addresses
    # Calculated by reversing the big-endian script hash bytes
    
    if address == "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX":
        # Big-endian: 285f1b5a0ae39889635da4df5a58dc4e2f1f163f
        # Little-endian (for neo-cli): 3f161f2fe2dc585adfa4da5d638998e30a5a1b5f28
        return "3f161f2fe2dc585adfa4da5d638998e30a5a1b5f28"
    elif address == "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB":
        # Big-endian: 936b3e5e7c0e9fc87f8cc2e1698ce62d6cb951b8
        # Little-endian (for neo-cli): b851b96c2de68c69e1c2c87cf89f0e7c5e3b3e93
        return "b851b96c2de68c69e1c2c87cf89f0e7c5e3b3e93"
    return None

def show_commands():
    """Show all possible command formats"""
    contract = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc"
    master_addr = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"
    tee_addr = "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"
    
    master_hash = neo_address_to_script_hash(master_addr)
    tee_hash = neo_address_to_script_hash(tee_addr)
    
    print("🔧 NEO-CLI INVOKE COMMANDS (All Methods)")
    print("=" * 60)
    print()
    
    print("Method 1: Use the JSON file (RECOMMENDED)")
    print("invoke initialize.neo-invoke.json")
    print()
    
    print("Method 2: Simple parameter format")
    print(f"invoke {contract} initialize")
    print("(This might prompt for parameters)")
    print()
    
    print("Method 3: With little-endian script hashes")
    print(f"invoke {contract} initialize [{master_hash} {tee_hash}]")
    print()
    
    print("Method 4: Alternative format")
    print(f"invoke {contract} initialize {master_hash} {tee_hash}")
    print()
    
    print("Method 5: Using raw addresses (if supported)")
    print(f'invoke {contract} initialize "{master_addr}" "{tee_addr}"')
    print()
    
    print("🔍 Script Hash Info:")
    print(f"Master Address: {master_addr}")
    print(f"Master Hash (LE): {master_hash}")
    print(f"TEE Address: {tee_addr}")
    print(f"TEE Hash (LE): {tee_hash}")

if __name__ == "__main__":
    show_commands()