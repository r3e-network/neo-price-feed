#!/bin/bash
cd /home/neo/git/neo-price-feed/neo-cli

echo "Starting neo-cli deployment..."

# Create a temporary command file for neo-cli
cat > temp-deploy-commands.txt << 'EOF'
create wallet temp-deploy.json
password123

import key KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb
list asset
deploy deploy/PriceFeed.Oracle.nef deploy/PriceFeed.Oracle.manifest.json
yes
exit
EOF

# Run deployment
./neo-cli < temp-deploy-commands.txt

# Clean up
rm -f temp-deploy-commands.txt temp-deploy.json