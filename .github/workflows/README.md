# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the Neo Price Feed project.

## Workflows Overview

### 1. Continuous Integration (`ci.yml`)
- **Trigger**: Push to master/main or pull requests
- **Purpose**: Comprehensive CI including build, test, and code quality checks
- **Jobs**:
  - `build-and-test`: Builds solution and runs fast tests (SlowTest excluded)
  - `code-quality`: Runs code formatting and static analysis
- **Features**: NuGet caching, test filtering, code coverage upload
- **Timeout**: 30 minutes (8 minutes for tests)

### 2. Build and Publish (`build-and-publish.yml`)
- **Trigger**: Push to master/main (with path filters), PRs, or manual dispatch
- **Purpose**: Build and publish Docker images for production use
- **Jobs**:
  - `build-and-test`: Quick .NET build validation
  - `build-and-push-image`: Docker image build and push to GHCR
- **Features**: Multi-stage build, GitHub Container Registry, caching
- **Output**: Docker images tagged with branch/SHA and latest
- **Timeout**: 30 minutes

### 3. Run Price Feed Service (`price-feed.yml`)
- **Trigger**: Every 4 hours via cron schedule or manual dispatch
- **Purpose**: Execute price feed service to update on-chain prices
- **Steps**:
  1. Sparse checkout (scripts only)
  2. Initialize contract if needed
  3. Pull latest Docker image
  4. Run price feed service with dual-signature support
  5. Test results and upload logs
- **Environment**: Production or testnet
- **Timeout**: 30 minutes

### 4. Contract Deployment (`contract-deployment.yml`)
- **Trigger**: Manual dispatch only
- **Purpose**: Deploy and manage Neo smart contracts
- **Actions**: verify, init-execute, deploy, full
- **Environment**: testnet or mainnet (with approval)
- **Features**: Contract verification, initialization, deployment
- **Timeout**: 30 minutes

### 5. Run Tests (`test.yml`)
- **Trigger**: Pull requests or manual dispatch
- **Purpose**: Comprehensive test suite for PRs
- **Features**: Full test execution including SlowTest category
- **Timeout**: 30 minutes (8 minutes for test execution)

## Key Design Decisions

1. **Separation of Concerns**: Build, test, and runtime workflows are separate
2. **Docker-based Deployment**: Price feed runs in container for consistency
3. **Sparse Checkout**: Runtime workflow only needs scripts, not full source
4. **Pre-built Images**: No compilation during scheduled runs
5. **Fast Builds**: Tests run separately to keep Docker builds quick
6. **Timeout Limits**: All workflows limited to 30 minutes maximum

## Environment Variables & Secrets

### Required Secrets
- `MASTER_ACCOUNT_ADDRESS`: Master account address for contract operations
- `MASTER_ACCOUNT_PRIVATE_KEY`: Master account private key (WIF format)
- `NEO_TEE_ACCOUNT_ADDRESS`: TEE account address for price updates
- `NEO_TEE_ACCOUNT_PRIVATE_KEY`: TEE account private key (WIF format)
- `ORACLE_CONTRACT_HASH`: Deployed contract script hash (0x format)
- `NEO_RPC_URL`: Neo RPC endpoint URL
- `COINMARKETCAP_API_KEY`: CoinMarketCap API key for price data

### Optional Configuration Variables
- `BATCH_SIZE`: Number of prices per batch (default: 10)
- `PRICE_UPDATE_INTERVAL_MINUTES`: Update interval (default: 15)
- `CONTRACT_GAS_FEE`: Gas fee per transaction (default: 0.05)
- `PRICE_FEED_API_URL`: Additional price data source API
- `NEO_RPC_ENDPOINT_MAINNET`: Mainnet RPC endpoint (for mainnet deployments)

### Consistency Notes
All workflows use standardized environment variable names:
- `ORACLE_CONTRACT_HASH` (not CONTRACT_SCRIPT_HASH)
- `NEO_RPC_URL` (not NEO_RPC_ENDPOINT)
- `NEO_TEE_ACCOUNT_*` prefix for TEE account variables

## Monitoring

- Workflow status: https://github.com/r3e-network/neo-price-feed/actions
- Use `scripts/check-workflow-status.py` to check recent runs
- Use `scripts/trigger-workflow.sh` to manually trigger workflows