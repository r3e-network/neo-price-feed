#!/bin/bash
# Neo-CLI Deployment Script

cd /home/neo/git/neo-price-feed/neo-cli

# Create deployment commands file
cat > deploy-commands.txt << 'EOF'
create wallet deploy-wallet.json
open wallet deploy-wallet.json
import key KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb
list asset
deploy deploy/PriceFeed.Oracle.nef deploy/PriceFeed.Oracle.manifest.json
EOF

echo "🚀 Starting Neo-CLI deployment..."

# Run Neo-CLI with commands
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    ./neo-cli.exe --config testnet.config.json < deploy-commands.txt
else
    ./neo-cli --config testnet.config.json < deploy-commands.txt
fi
