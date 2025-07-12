#!/bin/bash

echo "open wallet deploy-wallet.json
deploy123
deploy deploy/PriceFeed.Oracle.nef deploy/PriceFeed.Oracle.manifest.json
yes
exit" | ./neo-cli