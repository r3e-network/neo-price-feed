# Neo Price Feed Oracle - Contract Initialization Guide

## Contract Details

- **Contract Hash**: `0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc`
- **Transaction Hash**: `0x15ccc11dbe781c6878d04a713fb04bc7a9c1f162fee97d2f03014eca918c4a53`
- **Network**: Neo N3 TestNet
- **Deployment Date**: 2025-06-29

## Initialization Steps

The contract has been successfully deployed but needs to be initialized before use.

### Step 1: Open Neo-CLI

Navigate to your neo-cli directory and start it:

```bash
cd /home/neo/git/neo-price-feed/neo-cli
./neo-cli
```

### Step 2: Open Your Wallet

In neo-cli, open the wallet containing the master account:

```
neo> open wallet wallet.json
password: ********
```

### Step 3: Initialize the Contract

Run this command to initialize the contract with admin accounts:

```
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc initialize ["NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX","NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]
```

When prompted:
- Review the transaction details
- Type `yes` to relay the transaction
- Wait for confirmation

### Step 4: Add TEE Account as Oracle

After initialization is confirmed, add the TEE account as an authorized oracle:

```
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc addOracle ["NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]
```

Again, type `yes` when prompted to relay the transaction.

### Step 5: Set Minimum Oracles

Configure the minimum number of oracles required:

```
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc setMinOracles [1]
```

Type `yes` to relay the transaction.

### Step 6: Verify Initialization

Run these commands to verify the setup:

```
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc isInitialized []
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc getOracleCount []
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc isOracle ["NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc getMinOracles []
```

Expected results:
- `isInitialized`: Should return `true` (1)
- `getOracleCount`: Should return `1`
- `isOracle`: Should return `true` (1)
- `getMinOracles`: Should return `1`

## Testing the Oracle

After successful initialization:

### 1. Run the Price Feed Service

```bash
dotnet run --project src/PriceFeed.Console
```

### 2. Check Price Updates

In neo-cli, query prices:

```
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc getPrice ["BTCUSDT"]
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc getPrice ["ETHUSDT"]
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc getPrice ["NEOUSDT"]
```

### 3. Monitor on TestNet Explorer

View contract activity:
- Contract: https://testnet.explorer.onegate.space/contract/0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc
- Transactions: Check the contract's transaction history

## Troubleshooting

### "Access denied" Error
- Ensure you're using the master account wallet
- Check that the wallet is unlocked

### "Already initialized" Error
- The contract can only be initialized once
- Use verification commands to check current state

### "Insufficient GAS" Error
- Ensure your account has enough GAS for transactions
- Each initialization step costs approximately 0.1-0.5 GAS

### Transaction Not Confirming
- Check TestNet status
- Try alternative RPC endpoints:
  - http://seed2t5.neo.org:20332
  - http://seed3t5.neo.org:20332
  - http://seed4t5.neo.org:20332

## Security Notes

1. **Private Keys**: Never share or commit private keys
2. **TEE Account**: Keep separate from master account
3. **Access Control**: Only authorized accounts can update prices
4. **Initialization**: Can only be done once - be careful!

## Next Steps

After successful initialization:

1. ✅ Contract is initialized
2. ✅ TEE account is authorized
3. ✅ Minimum oracles configured
4. 🚀 Start price feed service
5. 📊 Monitor price updates
6. 🔍 Verify on TestNet explorer

Your Neo N3 Price Feed Oracle is now ready for production use on TestNet!