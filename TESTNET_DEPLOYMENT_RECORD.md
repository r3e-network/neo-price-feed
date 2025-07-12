# Neo Price Feed Oracle - TestNet Deployment Record

## Deployment Information

**Date**: 2025-06-29  
**Network**: Neo N3 TestNet  
**Deployer**: Neo-CLI v3.6.2

### Contract Details

- **Contract Hash**: `0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc`
- **Transaction Hash**: `0x15ccc11dbe781c6878d04a713fb04bc7a9c1f162fee97d2f03014eca918c4a53`
- **Deployment Cost**:
  - Gas Consumed: 10.00035859 GAS
  - Network Fee: 0.00184924 GAS
  - Total Fee: 10.00220783 GAS

### Contract Files

- **NEF File**: `/home/neo/git/neo-price-feed/deployment-files/PriceFeed.Oracle.nef`
- **Manifest**: `/home/neo/git/neo-price-feed/deployment-files/PriceFeed.Oracle.manifest.json`

### Deployment Account

- **Address**: `NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX`
- **Role**: Master Account (Deployment & Administration)

### TEE Account (for Price Updates)

- **Address**: `NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB`
- **Role**: TEE Account (Price Feed Operations)

## Verification

### TestNet Block Explorer

View the deployed contract on Neo TestNet explorer:
- Transaction: https://testnet.explorer.onegate.space/transaction/0x15ccc11dbe781c6878d04a713fb04bc7a9c1f162fee97d2f03014eca918c4a53
- Contract: https://testnet.explorer.onegate.space/contract/0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc

### RPC Endpoints

- Primary: `http://seed1t5.neo.org:20332`
- Alternative TestNet nodes:
  - `http://seed2t5.neo.org:20332`
  - `http://seed3t5.neo.org:20332`
  - `http://seed4t5.neo.org:20332`
  - `http://seed5t5.neo.org:20332`

## Post-Deployment Steps

### 1. Initialize Contract ✅
```bash
python3 scripts/initialize-contract.py
```

### 2. Add TEE Account
```bash
# The TEE account needs to be authorized in the contract
# This allows it to submit price updates
```

### 3. Verify Contract State
```bash
# Check if contract is initialized
# Check authorized accounts
# Test price retrieval
```

### 4. Start Price Feed Service
```bash
# Run the price feed service
dotnet run --project src/PriceFeed.Console
```

## Contract Methods

### Administrative Methods
- `initialize()` - Initialize the contract (one-time only)
- `addTeeAccount(address)` - Add authorized TEE account
- `removeTeeAccount(address)` - Remove authorized TEE account
- `addOracle(address)` - Add price oracle source
- `removeOracle(address)` - Remove price oracle source

### Price Feed Methods
- `updatePrice(symbol, price, timestamp)` - Update price for a symbol (TEE only)
- `updatePriceBatch(data[])` - Batch update multiple prices (TEE only)

### Query Methods
- `getPrice(symbol)` - Get current price for a symbol
- `getPriceWithTimestamp(symbol)` - Get price with timestamp
- `getLatestPrices(symbols[])` - Get multiple prices at once
- `isInitialized()` - Check if contract is initialized
- `isTeeAccount(address)` - Check if address is authorized TEE

## Supported Price Pairs

The oracle currently supports the following trading pairs:
- BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, ADAUSDT
- SOLUSDT, DOGEUSDT, DOTUSDT, MATICUSDT, LTCUSDT
- AVAXUSDT, LINKUSDT, UNIUSDT, ATOMUSDT
- NEOUSDT, GASUSDT, FLMUSDT
- SHIBUSDT, PEPEUSDT

## Security Considerations

1. **Private Keys**: Store securely, never commit to repository
2. **TEE Account**: Separate account for price updates (principle of least privilege)
3. **Multi-signature**: Consider implementing for production deployments
4. **Rate Limiting**: Contract implements update frequency limits
5. **Price Validation**: Contract validates price ranges and timestamps

## Monitoring

Monitor the contract and price feed service:
- Contract events via RPC
- Price update frequency
- Data source availability
- Transaction success rates

## Troubleshooting

### Common Issues

1. **"Contract not initialized"**
   - Run the initialization script
   
2. **"Unauthorized account"**
   - Ensure TEE account is added to contract
   
3. **"Price data stale"**
   - Check if price feed service is running
   - Verify data source API keys

### Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/neo-price-feed/issues
- Documentation: See project README.md