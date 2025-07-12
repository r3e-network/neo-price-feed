#!/bin/bash
echo "🚀 Neo N3 Contract Deployment Helper"
echo "===================================="
echo ""
echo "Files ready for deployment:"
echo "  - PriceFeed.Oracle.nef"
echo "  - PriceFeed.Oracle.manifest.json"
echo ""
echo "Account: NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX"
echo "Expected Contract Hash: 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc"
echo ""
echo "Choose deployment method:"
echo "1) Neo-CLI"
echo "2) NeoLine Browser Extension"
echo "3) Show deployment instructions"
echo ""
read -p "Select option (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Neo-CLI Instructions:"
        echo "1. Download: https://github.com/neo-project/neo-cli/releases"
        echo "2. Run: ./neo-cli"
        echo "3. Import key: KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb"
        echo "4. Deploy: deploy PriceFeed.Oracle.nef PriceFeed.Oracle.manifest.json"
        ;;
    2)
        echo ""
        echo "NeoLine Instructions:"
        echo "1. Install: https://neoline.io/"
        echo "2. Import wallet with WIF"
        echo "3. Switch to TestNet"
        echo "4. Upload contract files"
        ;;
    3)
        cat DEPLOYMENT_INSTRUCTIONS.md
        ;;
esac
