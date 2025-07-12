#!/bin/bash
cd /home/neo/git/neo-price-feed/neo-cli

echo "Starting deployment..."
(
echo "open wallet deploy-wallet.json"
sleep 1
echo ""
sleep 1  
echo "deploy deploy/PriceFeed.Oracle.nef deploy/PriceFeed.Oracle.manifest.json"
sleep 2
echo "yes"
sleep 1
echo "exit"
) | ./neo-cli