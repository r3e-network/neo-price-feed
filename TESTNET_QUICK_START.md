# 🚀 Neo N3 Price Feed - TestNet Quick Start Guide

## ✅ Current Status
- **Configuration**: ✅ Complete and tested
- **Workflow**: ✅ Working (collecting real prices)
- **Contract**: ⏳ Awaiting deployment

## 📊 Test Results
Successfully retrieved live cryptocurrency prices:
- **BTC**: $107,377.34
- **ETH**: $2,424.89
- **NEO**: $5.33

## 🔑 Your Credentials
```
Master Account: NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX
Private Key: KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb
Balance: 50 NEO + 50 GAS (TestNet)

TEE Account: NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB
```

## 🚀 Deploy Contract (Choose One Method)

### Method 1: Neo-CLI
```bash
wget https://github.com/neo-project/neo-cli/releases/download/v3.8.2/neo-cli-linux-x64.zip
unzip neo-cli-linux-x64.zip
cd neo-cli

# Start Neo-CLI
./neo-cli --network testnet

# In Neo-CLI console:
create wallet master.json
import key KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb
open wallet master.json
deploy /path/to/PriceFeed.Oracle.nef
```

### Method 2: Web Deployment
1. Go to https://neowallet.cn/
2. Switch to TestNet
3. Import wallet with your private key
4. Deploy contract through web interface

### Method 3: NeoLine Extension
1. Install NeoLine Chrome extension
2. Import account with private key
3. Switch to TestNet
4. Deploy via extension

## 📝 After Deployment

1. **Get your contract hash from deployment output**

2. **Update appsettings.json**:
```json
"ContractScriptHash": "0xYOUR_CONTRACT_HASH_HERE"
```

3. **Initialize contract** (in Neo-CLI):
```
invoke 0xYOUR_CONTRACT_HASH initialize ["NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX","NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]
invoke 0xYOUR_CONTRACT_HASH addOracle ["NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]
invoke 0xYOUR_CONTRACT_HASH setMinOracles [1]
```

4. **Run the complete workflow**:
```bash
dotnet run --project src/PriceFeed.Console --skip-health-checks
```

## 🔗 Useful Links
- **TestNet Explorer**: https://testnet.explorer.onegate.space/
- **Check Your Balance**: https://testnet.explorer.onegate.space/address/NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX
- **Neo Docs**: https://docs.neo.org/
- **TestNet Faucet**: https://neowish.ngd.network/

## 💡 Tips
- Contract deployment costs ~10 GAS
- Each price update transaction costs ~0.1 GAS
- Your 50 GAS is enough for ~400 price updates
- Monitor your balance and get more from faucet if needed

## 🎯 Success Indicators
After deployment, you should see:
- "Successfully processed batch" in logs
- Transaction hashes for each price update
- Prices stored on blockchain (check explorer)

---
**Need Help?** The workflow is fully functional - you just need to deploy the contract!