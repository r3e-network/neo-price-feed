# Neo Price Feed Oracle - Contract Setup Guide

## Current Status

### ✅ Contract Deployed
- **Contract Hash**: `0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc`
- **Network**: Neo N3 TestNet
- **Status**: Deployed but NOT initialized

### ❌ Contract Not Initialized
The contract needs to be initialized before it can accept price updates.

## Setup Options

### Option 1: Using ContractDeployer (Recommended)

The ContractDeployer tool provides RPC-based verification and initialization commands:

```bash
cd src/PriceFeed.ContractDeployer

# Verify current status
dotnet run verify

# Get initialization commands
dotnet run init

# Full setup flow (deploy info + init commands + verify)
dotnet run full
```

### Option 2: Using Python Script

```bash
# Run the RPC initialization script
python3 scripts/initialize-contract-rpc.py
```

### Option 3: Manual neo-cli Commands

Execute these commands in neo-cli:

```bash
# 1. Connect to TestNet
connect http://seed1t5.neo.org:20332

# 2. Import the owner's private key (if not already imported)
import key KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb

# 3. Initialize the contract
invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc initialize ["NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX","NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"] NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX

# 4. Add TEE as oracle
invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc addOracle ["NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"] NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX

# 5. Set minimum oracles to 1
invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc setMinOracles [1] NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX
```

## Verification

After initialization, verify the contract state:

```bash
# Using ContractDeployer
cd src/PriceFeed.ContractDeployer
dotnet run verify

# Using Python script
python3 scripts/verify-system.py
```

Expected output after successful initialization:
- Owner: NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX
- TEE Accounts: 1 configured
- Oracles: 1 configured
- Min Oracles: 1

## Automatic Price Updates

Once initialized, GitHub Actions will automatically:
- Run every 5 minutes
- Fetch prices from multiple sources (CoinGecko, Kraken, Coinbase)
- Send batch transactions with dual signatures (TEE + Master)
- Update prices for configured symbols

## Monitoring

Check GitHub Actions logs for price feed status:
- Go to the repository's Actions tab
- Look for "Neo Price Feed - TestNet" workflow runs
- Each run shows price fetching and transaction submission status

## Troubleshooting

### Contract Not Initialized
- Ensure you have sufficient GAS (minimum 1 GAS for initialization)
- Use the correct owner account for initialization
- Contract can only be initialized once

### Price Updates Not Working
- Verify contract is initialized: `dotnet run verify`
- Check GitHub Actions workflow is enabled
- Ensure TEE and Master accounts have sufficient GAS
- Review GitHub Actions logs for errors

### Transaction Failures
- Check account balances (both TEE and Master need GAS)
- Verify contract is not paused
- Ensure price sources are accessible

## Account Information

- **Master Account**: NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX
- **TEE Account**: NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB
- **Contract**: 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc

## Next Steps

1. Initialize the contract using one of the methods above
2. Verify initialization was successful
3. Monitor GitHub Actions for automatic price updates
4. Check contract for price data after first update cycle