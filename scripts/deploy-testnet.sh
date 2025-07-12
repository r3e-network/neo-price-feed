#\!/bin/bash

# Neo N3 TestNet Deployment Script
set -e

# Configuration
RPC_ENDPOINT="${RPC_ENDPOINT:-http://seed1t5.neo.org:20332}"
OWNER_ADDRESS="${OWNER_ADDRESS:-NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX}"
OWNER_PRIVATE_KEY="${OWNER_PRIVATE_KEY:-KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb}"
TEE_ACCOUNT_ADDRESS="${TEE_ACCOUNT_ADDRESS:-NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB}"

echo "=== Neo N3 TestNet Deployment Script ==="
echo "RPC Endpoint: $RPC_ENDPOINT"
echo "Owner Address: $OWNER_ADDRESS"
echo "TEE Account: $TEE_ACCOUNT_ADDRESS"
echo ""

# Step 1: Compile the smart contract
echo "Step 1: Compiling PriceOracle contract..."
CONTRACT_PATH="src/PriceFeed.Contracts"

if [ \! -d "$CONTRACT_PATH" ]; then
    echo "Error: Contract directory not found: $CONTRACT_PATH"
    exit 1
fi

cd "$CONTRACT_PATH"

# Build the contract
echo "Building contract..."
dotnet build --configuration Release

if [ $? -ne 0 ]; then
    echo "Error: Contract compilation failed"
    exit 1
fi

# Find the compiled NEF and manifest files
NEF_FILE=$(find bin/Release/net8.0 -name "*.nef"  < /dev/null |  head -1)
MANIFEST_FILE=$(find bin/Release/net8.0 -name "*.manifest.json" | head -1)

if [ -z "$NEF_FILE" ] || [ -z "$MANIFEST_FILE" ]; then
    echo "Error: Compiled contract files not found"
    exit 1
fi

echo "✓ Contract compiled successfully"
echo "  NEF file: $NEF_FILE"
echo "  Manifest: $MANIFEST_FILE"

cd - > /dev/null

echo "=== Deployment Preparation Complete ==="
echo ""
echo "Contract files are ready for deployment!"
echo ""
echo "To deploy to TestNet:"
echo "1. Use neo-cli or neo-gui to deploy the contract"
echo "2. Initialize with your accounts"
echo "3. Update appsettings.json with the contract hash"
