# Neo N3 Price Feed Service with TEE

A production-ready price feed service for Neo N3 blockchain that leverages a Trusted Execution Environment (TEE). The service fetches data from multiple sources, aggregates it, and submits it to a smart contract on-chain using a dual-signature transaction system.

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

## Features

- **Multi-Source Data Collection**: Fetches price data from multiple sources:
  - Binance
  - CoinMarketCap
  - Coinbase
  - OKEx
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
- Collects price data from multiple sources (Binance, CoinMarketCap, Coinbase, OKEx)
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

- **PriceFeed.Core**: Contains domain models, interfaces, and core business logic
- **PriceFeed.Infrastructure**: Contains implementations of data sources, services, and external integrations
- **PriceFeed.Console**: The console application that runs in GitHub Actions
- **PriceFeed.Contracts**: Contains the Neo N3 smart contract for the price oracle
- **PriceFeed.Tests**: Contains unit tests for the solution

## Architecture

The solution is structured into the following projects:

- **PriceFeed.Core**: Contains domain models and interfaces
- **PriceFeed.Infrastructure**: Implements data source adapters and services
- **PriceFeed.Console**: Console application that runs in the TEE
- **PriceFeed.Contracts**: Contains the Neo smart contract
- **PriceFeed.Tests**: Contains unit tests

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
- `NEO_CONTRACT_HASH`: Script hash of the deployed contract
- `NEO_WALLET_WIF`: WIF of the wallet to use for signing transactions

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
    "ContractScriptHash": "0xd2a4cff31913016155e38e474a2c06d08be276cf",
    "WalletWif": "KxDgvEKzgSBPPfuVfw67oPQBSjidEiqTHURKSDL1R7yGaGYAeYnr",
    "MaxBatchSize": 50
  }
}
```

### Running the Application

#### Local Development

```bash
# Run the price feed service
cd PriceFeed.Console
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

For detailed information about the smart contract, see the [contract documentation](PriceFeed.Contracts/README.md).

## GitHub Actions Workflow

The price feed service is configured to run in a GitHub Actions workflow, which serves as our Trusted Execution Environment (TEE). The workflow is defined in `.github/workflows/price-feed.yml`:

```yaml
name: Neo Price Feed Service

on:
  schedule:
    # Run once per week on Monday at 00:00 UTC
    - cron: '0 0 * * 1'
  workflow_dispatch:  # Allow manual triggering

jobs:
  run-price-feed:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Required for attestation
      contents: read

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Setup .NET
      uses: actions/setup-dotnet@v3
      with:
        dotnet-version: 9.0.x

    - name: Restore dependencies
      run: dotnet restore

    - name: Build
      run: dotnet build --configuration Release --no-restore

    - name: Run Price Feed
      run: dotnet run --project PriceFeed.Console/PriceFeed.Console.csproj --configuration Release
      env:
        BINANCE_API_KEY: ${{ secrets.BINANCE_API_KEY }}
        BINANCE_API_SECRET: ${{ secrets.BINANCE_API_SECRET }}
        COINMARKETCAP_API_KEY: ${{ secrets.COINMARKETCAP_API_KEY }}
        COINBASE_API_KEY: ${{ secrets.COINBASE_API_KEY }}
        COINBASE_API_SECRET: ${{ secrets.COINBASE_API_SECRET }}
        OKEX_API_KEY: ${{ secrets.OKEX_API_KEY }}
        OKEX_API_SECRET: ${{ secrets.OKEX_API_SECRET }}
        OKEX_PASSPHRASE: ${{ secrets.OKEX_PASSPHRASE }}
        NEO_RPC_ENDPOINT: ${{ secrets.NEO_RPC_ENDPOINT }}
        NEO_CONTRACT_HASH: ${{ secrets.NEO_CONTRACT_HASH }}
        NEO_ACCOUNT_ADDRESS: ${{ secrets.NEO_ACCOUNT_ADDRESS }}
        NEO_ACCOUNT_PRIVATE_KEY: ${{ secrets.NEO_ACCOUNT_PRIVATE_KEY }}
        NEO_MASTER_ACCOUNT_PRIVATE_KEY: ${{ secrets.NEO_MASTER_ACCOUNT_PRIVATE_KEY }}
        SYMBOLS: "NEOBTC,NEOUSDT,BTCUSDT,FLMUSDT"
```

### Configuring the Workflow

1. **Schedule**: The workflow is configured to run once per week (Monday at 00:00 UTC) by default. You can adjust the schedule by modifying the cron expression in the workflow file.

2. **Manual Triggering**: You can also trigger the workflow manually using the GitHub Actions UI.

3. **Environment Variables**: All sensitive configuration is stored in GitHub Secrets and passed to the application as environment variables.

4. **Symbols**: The `SYMBOLS` environment variable defines which trading pairs to include in the price feed. You can add or remove symbols as needed.

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
