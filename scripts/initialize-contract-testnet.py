#!/usr/bin/env python3
"""
Initialize the Neo Price Feed Oracle contract on TestNet.
This script performs the initialization steps programmatically instead of using neo-cli manually.
"""

import os
import sys
import json
import asyncio
from neo3 import wallet
from neo3.api import AsyncRPCClient, JSONRPCException
from neo3.core import types
from neo3.contracts import contract

# Contract details
CONTRACT_HASH = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc"
TESTNET_RPC = "http://seed1t5.neo.org:20332"

# Account addresses from the initialization guide
MASTER_ACCOUNT = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"
TEE_ACCOUNT = "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"


async def check_initialization_status(client):
    """Check if the contract is already initialized."""
    try:
        script = contract.build_invoke_script(
            CONTRACT_HASH,
            "isInitialized",
            []
        )
        result = await client.invoke_script(script)
        
        if result.state == "HALT":
            # The result stack should contain a boolean value
            if result.stack and len(result.stack) > 0:
                return bool(result.stack[0].value)
        return False
    except Exception as e:
        print(f"Error checking initialization status: {e}")
        return False


async def invoke_contract_method(client, method_name, params):
    """Invoke a contract method (read-only)."""
    try:
        script = contract.build_invoke_script(
            CONTRACT_HASH,
            method_name,
            params
        )
        result = await client.invoke_script(script)
        
        if result.state == "HALT":
            return result
        else:
            print(f"Method {method_name} failed with state: {result.state}")
            if result.exception:
                print(f"Exception: {result.exception}")
            return None
    except Exception as e:
        print(f"Error invoking {method_name}: {e}")
        return None


async def verify_contract_state(client):
    """Verify the current state of the contract."""
    print("\n=== Verifying Contract State ===")
    
    # Check if initialized
    is_initialized = await check_initialization_status(client)
    print(f"Is Initialized: {is_initialized}")
    
    if is_initialized:
        # Check oracle count
        result = await invoke_contract_method(client, "getOracleCount", [])
        if result and result.stack:
            print(f"Oracle Count: {result.stack[0].value}")
        
        # Check if TEE account is oracle
        result = await invoke_contract_method(client, "isOracle", [TEE_ACCOUNT])
        if result and result.stack:
            is_oracle = bool(result.stack[0].value)
            print(f"TEE Account is Oracle: {is_oracle}")
        
        # Check minimum oracles
        result = await invoke_contract_method(client, "getMinOracles", [])
        if result and result.stack:
            print(f"Minimum Oracles: {result.stack[0].value}")
    
    return is_initialized


async def test_price_query(client):
    """Test querying prices from the contract."""
    print("\n=== Testing Price Queries ===")
    
    symbols = ["BTCUSDT", "ETHUSDT", "NEOUSDT"]
    
    for symbol in symbols:
        result = await invoke_contract_method(client, "getPrice", [symbol])
        if result and result.stack:
            if len(result.stack) > 0:
                price = result.stack[0].value
                print(f"{symbol}: {price}")
            else:
                print(f"{symbol}: No price data")
        else:
            print(f"{symbol}: Query failed")


async def main():
    """Main function to check contract status."""
    print("Neo Price Feed Oracle - Contract Status Check")
    print(f"Contract Hash: {CONTRACT_HASH}")
    print(f"Network: TestNet")
    print(f"RPC Endpoint: {TESTNET_RPC}")
    
    async with AsyncRPCClient(TESTNET_RPC) as client:
        try:
            # Check if we can connect to the network
            version = await client.get_version()
            print(f"\nConnected to Neo node version: {version['useragent']}")
            
            # Verify contract state
            is_initialized = await verify_contract_state(client)
            
            if is_initialized:
                # Test price queries
                await test_price_query(client)
                
                print("\n✅ Contract is initialized and ready for use!")
                print("\nTo submit prices, run:")
                print("  dotnet run --project src/PriceFeed.Console")
            else:
                print("\n⚠️  Contract is not initialized!")
                print("\nInitialization requires:")
                print("1. Access to the master account wallet")
                print("2. Manual execution via neo-cli")
                print("3. Sufficient GAS for transactions")
                print("\nPlease follow the INITIALIZATION_GUIDE.md for manual initialization.")
        
        except JSONRPCException as e:
            print(f"\nRPC Error: {e}")
            print("The TestNet node might be unavailable. Try alternative endpoints:")
            print("- http://seed2t5.neo.org:20332")
            print("- http://seed3t5.neo.org:20332")
            print("- http://seed4t5.neo.org:20332")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # Check if neo3 library is installed
    try:
        import neo3
    except ImportError:
        print("Error: neo3 library is not installed.")
        print("Please install it with: pip install neo3-python")
        sys.exit(1)
    
    asyncio.run(main())