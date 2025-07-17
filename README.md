# Neo N3 Price Feed Service with TEE

A production-ready price feed service for Neo N3 blockchain that leverages a Trusted Execution Environment (TEE). The service fetches data from multiple sources, aggregates it, and submits it to a smart contract on-chain using a dual-signature transaction system.

## ⚠️ Important: API Accessibility Notice

Many popular cryptocurrency APIs have accessibility restrictions due to regional regulations, API key requirements, or domain blocks. Please see [Accessible APIs Guide](docs/accessible-apis.md) for information about which data sources are accessible in your region and recommended alternatives.

**Quick Start with Accessible APIs:**
- Use the `appsettings.accessible.json` configuration for maximum compatibility
- Primary recommended sources: CoinGecko, Kraken
- See the [accessibility guide](docs/accessible-apis.md) for detailed setup instructions

## Security Model

This service leverages a Trusted Execution Environment (TEE) for secure operation:

1. **Dual-Signature Transactions**: Two Neo accounts are used for each transaction:
   - **TEE Account**: Generated within the TEE, used to authenticate that transactions are truly generated in the secure environment
   - **Master Account**: Set by you as a secret, contains GAS for transaction fees
2. **Secure Execution**: The private keys are only accessible within the TEE
3. **Persistent Identity**: The same accounts are used across all price feed transactions
4. **Isolation**: The TEE provides a clean, isolated environment for each execution
5. **Account Persistence**: The accounts persist across code updates, ensuring a consistent identity
6. **Asset Transfer**: Any assets received by the TEE account are automatically transferred to the Master account

For detailed information, see:
- [TEE Implementation](docs/tee-implementation.md)
- [Dual-Signature Transactions](docs/dual-signature-transactions.md)
- [Account Persistence](docs/account-persistence.md)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/r3e-network/neo-price-feed)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![.NET](https://img.shields.io/badge/.NET-9.0-purple.svg)](https://dotnet.microsoft.com/download/dotnet/9.0)
[![Neo](https://img.shields.io/badge/Neo-N3-green.svg)](https://neo.org/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://r3e-network.github.io/neo-price-feed/)

## 🚀 Live Deployment Status

**⚠️ DEPLOYED BUT NOT INITIALIZED ON NEO N3 TESTNET**

- **Contract Hash**: `0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc`
- **Network**: Neo N3 TestNet
- **Status**: 🟡 **NEEDS INITIALIZATION** - Contract deployed but not yet initialized
- **TEE Account**: `NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB`
- **Next Step**: Run initialization commands below

📊 **Monitoring**:
- Contract Hash: `0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc` (verified on-chain)
- [GitHub Actions Status](https://github.com/r3e-network/neo-price-feed/actions)
- [Price Feed Workflow](https://github.com/r3e-network/neo-price-feed/actions/workflows/price-feed.yml)

⚠️ **Action Required**: Run `./scripts/one-command-init.sh` to initialize the contract (takes ~30 seconds).

## Supported Cryptocurrencies

The price oracle currently tracks **19+ major cryptocurrencies** including:

- **BTC/USDT** - Bitcoin
- **ETH/USDT** - Ethereum  
- **ADA/USDT** - Cardano
- **BNB/USDT** - Binance Coin
- **XRP/USDT** - Ripple
- **SOL/USDT** - Solana
- **MATIC/USDT** - Polygon
- **DOT/USDT** - Polkadot
- **LINK/USDT** - Chainlink
- **UNI/USDT** - Uniswap
- **And more...**

*Price data is aggregated from multiple sources for accuracy and reliability.*

## Contract Management

⚠️ **Contract needs initialization.** Use this simple one-command process:

## 🚀 One-Command Initialization

```bash
# Set your Master Account private key (WIF format)
export MASTER_WIF="your_master_account_private_key_here"

# Run the initialization script
./scripts/one-command-init.sh
```

**That's it!** The script will:
1. ✅ Install neo-mamba if needed
2. ✅ Initialize the contract with owner and TEE account
3. ✅ Add TEE account as an authorized oracle
4. ✅ Set minimum oracles to 1
5. ✅ Verify everything is working

## 📋 Manual Process (Alternative)

If you prefer manual control:

```bash
# Install neo-mamba
pip install neo-mamba

# Initialize contract (replace YOUR_WIF with your Master Account WIF)
neo-mamba contract invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc initialize "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX" "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB" --wallet-wif YOUR_WIF --rpc http://seed1t5.neo.org:20332 --force

# Add TEE as oracle
neo-mamba contract invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc addOracle "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB" --wallet-wif YOUR_WIF --rpc http://seed1t5.neo.org:20332 --force

# Set minimum oracles
neo-mamba contract invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc setMinOracles 1 --wallet-wif YOUR_WIF --rpc http://seed1t5.neo.org:20332 --force
```

## 🔍 Verify Status

Check if initialization was successful:

```bash
python3 scripts/quick-initialize.py
```

## Features

- **Multi-Source Data Collection**: Fetches price data from multiple sources:
  - CoinGecko (✅ Accessible)
  - Kraken (✅ Accessible)
  - Coinbase (✅ Partially Accessible)
  - Binance (❌ Regionally Restricted)
  - CoinMarketCap (❌ Requires API Key)
  - OKEx (❌ Domain Restrictions)
- **Advanced Aggregation**: Aggregates price data using volume-weighted average or simple average
- **Confidence Scoring**: Calculates confidence scores based on standard deviation and number of sources
- **Batch Processing**: Sends batched price updates to a Neo smart contract
- **TEE Integration**: Runs periodically in a secure Trusted Execution Environment
- **Production-Ready**:
  - Comprehensive error handling and logging
  - Environment variables for configuration
  - Secure secrets management
  - Detailed execution logs
  - Fallback mechanisms when data sources are unavailable

## Solution Components

The solution consists of two main components:

### 1. Price Feed Service with TEE

A .NET console application that runs in a Trusted Execution Environment (TEE). The service:
- Collects price data from multiple sources (CoinGecko, Kraken, Coinbase, and others)
- Aggregates the data with confidence scoring
- Uses a dual-signature system with TEE and Master accounts
- Signs and submits transactions to the blockchain
- Creates cryptographic attestations to prove execution within the TEE
- Maintains the same accounts across code updates for a consistent identity

**Note**: This is not a web API service. It's designed to be triggered on a schedule to update price data.

### 2. Price Oracle Contract

A Neo N3 smart contract that stores price data on the blockchain and makes it available to other contracts and applications. The contract implements dual-signature verification:

- **TEE Account Signature**: Verifies that the transaction was generated in the GitHub Actions environment
- **Master Account Signature**: Provides the GAS for transaction fees
- **Asset Transfer**: Automatically transfers any assets from the TEE account to the Master account

## Project Structure

```
neo-price-feed/
├── src/                          # Source code
│   ├── PriceFeed.Core/          # Domain models and interfaces
│   ├── PriceFeed.Infrastructure/ # External integrations and services
│   ├── PriceFeed.Console/       # Console application entry point
│   └── PriceFeed.Contracts/     # Smart contracts
├── test/                        # Test projects
│   └── PriceFeed.Tests/         # Unit and integration tests
├── docs/                        # Documentation
├── scripts/                     # Build and deployment scripts
├── config/                      # Configuration templates
└── .github/                     # GitHub workflows and templates
```

### Components

- **PriceFeed.Core**: Contains domain models, interfaces, and core business logic
- **PriceFeed.Infrastructure**: Contains implementations of data sources, services, and external integrations
- **PriceFeed.Console**: The console application that runs in the TEE
- **PriceFeed.Contracts**: Contains the Neo N3 smart contract for the price oracle
- **PriceFeed.Tests**: Contains comprehensive unit and integration tests

### System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Data Sources   │────▶│  Price Feed     │────▶│  Neo Blockchain │
│  (Binance, etc) │     │  Console App    │     │  Smart Contract │
│                 │     │  (Secure TEE)   │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │                 │
                                               │  Smart Contract │
                                               │  Consumers      │
                                               │                 │
                                               └─────────────────┘
```

## Getting Started

### Prerequisites

- .NET 9.0 SDK
- Trusted Execution Environment setup
- Neo blockchain node (for contract deployment)

### Configuration

The application can be configured using environment variables in the TEE:

**Data Source API Keys:**
- `BINANCE_API_KEY`: API key for Binance
- `BINANCE_API_SECRET`: API secret for Binance
- `COINMARKETCAP_API_KEY`: API key for CoinMarketCap
- `COINBASE_API_KEY`: API key for Coinbase
- `COINBASE_API_SECRET`: API secret for Coinbase
- `OKEX_API_KEY`: API key for OKEx
- `OKEX_API_SECRET`: API secret for OKEx
- `OKEX_PASSPHRASE`: Passphrase for OKEx API

**Neo Blockchain Configuration:**
- `NEO_RPC_ENDPOINT`: Neo RPC endpoint URL
- `CONTRACT_SCRIPT_HASH`: Script hash of the deployed contract
- `TEE_ACCOUNT_ADDRESS`: TEE account address
- `TEE_ACCOUNT_PRIVATE_KEY`: TEE account private key (WIF format)
- `MASTER_ACCOUNT_ADDRESS`: Master account address
- `MASTER_ACCOUNT_PRIVATE_KEY`: Master account private key (WIF format)

**General Configuration:**
- `SYMBOLS`: Comma-separated list of symbols to collect price data for (e.g., "BTCUSDT,ETHUSDT,NEOUSDT")

These environment variables are securely stored in the TEE.

For configuring different symbol formats for different data sources, see [Symbol Mappings](docs/symbol-mappings.md).

Alternatively, you can use the `appsettings.json` file for local development:

```json
{
  "PriceFeed": {
    "Symbols": ["NEOBTC", "NEOUSDT", "BTCUSDT", "ETHUSDT"]
  },
  "Binance": {
    "BaseUrl": "https://api.binance.com",
    "TickerPriceEndpoint": "/api/v3/ticker/price",
    "Ticker24hEndpoint": "/api/v3/ticker/24hr",
    "ExchangeInfoEndpoint": "/api/v3/exchangeInfo",
    "TimeoutSeconds": 30
  },
  "CoinMarketCap": {
    "BaseUrl": "https://pro-api.coinmarketcap.com",
    "LatestQuotesEndpoint": "/v1/cryptocurrency/quotes/latest",
    "TimeoutSeconds": 30
  },
  "Coinbase": {
    "BaseUrl": "https://api.coinbase.com",
    "ExchangeRatesEndpoint": "/v2/exchange-rates",
    "SpotPriceEndpoint": "/v2/prices",
    "TimeoutSeconds": 30
  },
  "OKEx": {
    "BaseUrl": "https://www.okex.com",
    "TickerEndpoint": "/api/v5/market/ticker",
    "TimeoutSeconds": 30
  },
  "BatchProcessing": {
    "RpcEndpoint": "http://localhost:10332",
    "ContractScriptHash": "MUST_BE_SET_TO_YOUR_DEPLOYED_CONTRACT_HASH",
    "WalletWif": "MUST_BE_SET_VIA_ENVIRONMENT_VARIABLE",
    "MaxBatchSize": 50
  }
}
```

### Running the Application

#### Local Development

```bash
# Run the price feed service
cd src/PriceFeed.Console
dotnet run

# Test symbol mappings
dotnet run -- --test-symbol-mappings

# Test with mock price feed (for development)
dotnet run -- --test-mock-price-feed
```

#### Command-Line Options

The application supports the following command-line options:

| Option | Description |
|--------|-------------|
| `--test-symbol-mappings` | Test symbol mappings configuration and exit. |
| `--test-price-feed` | Run the price feed service with test data and exit. |
| `--test-mock-price-feed` | Run the price feed service with mock data sources and exit. |
| `--generate-account` | Generate a new Neo account for use with the price feed service. |
| `--continuous` | Run in continuous execution mode. |
| `--duration <minutes>` | Duration for continuous execution (default: 5 minutes). |
| `--interval <seconds>` | Update interval in continuous mode (default: 15 seconds). |
| `--help` | Display help information. |

#### Configuring Intervals

The price feed service runs on a schedule defined by a cron expression in the GitHub Actions workflow file:

```yaml
# In .github/workflows/scheduled-price-feed.yml
on:
  schedule:
    # Run once per week on Monday at 00:00 UTC
    - cron: '0 0 * * 1'
```

To change how often the service runs, simply update the cron expression in the workflow file.

For more information, see the [Configuring Intervals Documentation](docs/configuring-intervals.md).

#### Trusted Execution Environment

The application is configured to run automatically in the TEE on a schedule (once per week by default). It can also be triggered manually when needed.

### Running Tests

```bash
# Run all tests
dotnet test

# Run tests with coverage
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=opencover
```

## Logging

The application outputs detailed logs to the TEE console. These logs include:

- Price data collection from each source
- Aggregation results
- Batch processing status
- Detailed price information for each symbol

The application uses Serilog for structured logging. When running locally, logs are written to the console with a clear, readable format.

## Smart Contract

The solution includes a production-ready Neo N3 smart contract (`PriceOracleContract`) that:

- Stores price data on the blockchain
- Provides methods for querying price data
- Supports batch updates for efficiency
- Implements access control for oracles and admin operations
- Includes price deviation protection
- Supports contract upgrades
- Has a pause mechanism for emergencies
- Validates data quality through confidence scores

For detailed information about the smart contract, see the [contract documentation](src/PriceFeed.Contracts/README.md).

## 🤖 Automated Deployment & Operations

### Production Automation

The price oracle operates with **full automation** using GitHub Actions as the Trusted Execution Environment:

**🔄 Active Workflows:**
- **Price Feed Service**: Runs every 10 minutes automatically (`*/10 * * * *`)
- **Continuous Integration**: Tests on every push/PR  
- **Docker Build & Publish**: Builds container images for deployment
- **Contract Operations**: Manual deployment and management tools

### Current Schedule
```
Every 10 minutes: Workflow starts and runs for 5 minutes
  - Updates prices every 15 seconds during execution
  - ~20 price updates per workflow run
  - ~2,880 price updates per day
```

✅ **Continuous Execution Benefits**:
- Ultra-fresh price data (15-second intervals during active periods)
- Efficient resource utilization (5 minutes active, 5 minutes idle)
- Optimized GitHub Actions usage (~21,600 minutes/month)
- Respects API rate limits with interval spacing
- Maximizes price freshness while controlling costs

### Workflow Architecture

**1. Build Pipeline** (`.github/workflows/build-and-publish.yml`):
```yaml
# Builds and publishes Docker images to GitHub Container Registry
- Build .NET 9.0 solution (excluding contracts)
- Create multi-platform Docker image
- Push to ghcr.io/r3e-network/neo-price-feed:latest
```

**2. Price Feed Automation** (`.github/workflows/price-feed.yml`):
```yaml
# Runs price oracle every 10 minutes with continuous execution
on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
  workflow_dispatch:       # Manual trigger available

jobs:
  run-price-feed:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    environment: production  # Protected environment
    
    steps:
      - Sparse checkout (scripts only)
      - Initialize contract if needed  
      - Pull latest Docker image
      - Run price feed in continuous mode:
        docker run ... --continuous --duration 5 --interval 15
      - Test results and upload logs
```

**3. Environment Variables**: All sensitive data is stored as GitHub Secrets:
```bash
# Required secrets for production deployment
MASTER_ACCOUNT_ADDRESS      # Master account for transaction fees
MASTER_ACCOUNT_PRIVATE_KEY  # Master account private key (WIF format)
NEO_TEE_ACCOUNT_ADDRESS     # TEE account address
NEO_TEE_ACCOUNT_PRIVATE_KEY # TEE account private key (WIF format)
ORACLE_CONTRACT_HASH        # Deployed contract hash
NEO_RPC_URL                 # Neo RPC endpoint
COINMARKETCAP_API_KEY       # Price data API key
```

### Monitoring & Management

**📊 Real-time Monitoring:**
- [Live Workflow Runs](https://github.com/r3e-network/neo-price-feed/actions/workflows/price-feed.yml)
- [Contract on Explorer](https://testnet.explorer.onegate.space/contract/0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc)
- [All GitHub Actions](https://github.com/r3e-network/neo-price-feed/actions)

**🎛️ Manual Operations:**
- **Trigger Price Feed**: Use "Run workflow" button in GitHub Actions
- **Contract Management**: Run contract deployment workflow for admin operations
- **Emergency Stop**: Disable scheduled workflow in repository settings

## Security Considerations

- Sensitive configuration is stored in GitHub Secrets
- Environment variables are used to pass configuration to the application
- The wallet WIF is securely stored and never exposed in logs
- The application runs in an isolated GitHub Actions environment

## Troubleshooting

### Common Issues

#### Connection Issues

If you encounter connection issues, you can:

1. Check the RPC endpoint is accessible and responding
2. Verify the contract hash is correct and the contract is deployed
3. Ensure the Neo account has sufficient GAS for transactions

#### Data Source Issues

If you encounter issues with data sources:

1. Verify API keys are correct and have the necessary permissions
2. Check network connectivity to the data source APIs
3. Ensure symbol mappings are correctly configured for each data source

#### Transaction Failures

If transactions fail to be processed:

1. Check that the Neo RPC endpoint is accessible
2. Verify the contract hash is correct
3. Ensure the Neo account has sufficient GAS
4. Check the contract's access control settings

### Logs

The application outputs detailed logs that can help diagnose issues:

```
[2023-06-01 12:00:00 INF] Starting price feed service
[2023-06-01 12:00:01 INF] Collecting price data for symbols: BTCUSDT, ETHUSDT, NEOUSDT
[2023-06-01 12:00:02 INF] Aggregating price data
[2023-06-01 12:00:03 INF] Processing batch with 3 price updates
[2023-06-01 12:00:04 INF] Successfully processed batch
```

For more detailed logging, you can modify the logging level in `appsettings.json`.

## Documentation

Comprehensive documentation is available on GitHub Pages:

- [Main Documentation](https://github.com/r3e-network/neo-price-feed)
- [Price Feed Service Documentation](docs/service.md)
- [Price Oracle Contract Documentation](docs/contract.md)
- [Dual-Signature Transactions](docs/dual-signature-transactions.md)
- [Account Persistence](docs/account-persistence.md)
- [Configuring Intervals](docs/configuring-intervals.md)
- [Symbol Mappings](docs/symbol-mappings.md)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
