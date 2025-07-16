# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the Neo Price Feed project.

## Workflows

### 1. Build and Publish (`build-and-publish.yml`)
- **Trigger**: On push to master/main, PRs, or manual dispatch
- **Purpose**: Build and publish Docker images
- **Steps**:
  1. Run .NET build (tests removed for speed)
  2. Build Docker image
  3. Push to GitHub Container Registry (ghcr.io)
- **Output**: Docker image tagged with branch/SHA
- **Timeout**: 30 minutes

### 2. Run Price Feed Service (`price-feed.yml`)
- **Trigger**: Every 4 hours via cron schedule or manual dispatch
- **Purpose**: Run the price feed service using pre-built Docker image
- **Steps**:
  1. Check out scripts only (sparse checkout)
  2. Initialize contract if needed
  3. Pull and run latest Docker image
  4. Test price feed results
  5. Upload logs
- **No building**: Uses pre-built Docker image from registry
- **Timeout**: 30 minutes

### 3. Contract Deployment (`contract-deployment.yml`)
- **Trigger**: Manual dispatch only
- **Purpose**: Deploy smart contracts to Neo blockchain
- **Environment**: Requires approval for production
- **Timeout**: 30 minutes

### 4. Run Tests (`test.yml`)
- **Trigger**: Pull requests or manual dispatch
- **Purpose**: Run unit tests separately from build
- **Steps**:
  1. Build solution
  2. Run tests with parallelization
  3. Upload test results
- **Timeout**: 30 minutes (10 minutes for test execution)

## Key Design Decisions

1. **Separation of Concerns**: Build, test, and runtime workflows are separate
2. **Docker-based Deployment**: Price feed runs in container for consistency
3. **Sparse Checkout**: Runtime workflow only needs scripts, not full source
4. **Pre-built Images**: No compilation during scheduled runs
5. **Fast Builds**: Tests run separately to keep Docker builds quick
6. **Timeout Limits**: All workflows limited to 30 minutes maximum

## Environment Variables

Required secrets:
- `MASTER_ACCOUNT_PRIVATE_KEY`: Master account for contract operations
- `TEE_ACCOUNT_PRIVATE_KEY`: TEE account for price updates
- `ORACLE_CONTRACT_HASH`: Deployed contract hash
- `NEO_RPC_URL`: Neo RPC endpoint
- `PRICE_FEED_API_URL`: Price data source API

Optional configuration variables:
- `BATCH_SIZE`: Number of prices per batch (default: 10)
- `PRICE_UPDATE_INTERVAL_MINUTES`: Update interval (default: 15)
- `CONTRACT_GAS_FEE`: Gas fee per transaction (default: 0.05)

## Monitoring

- Workflow status: https://github.com/r3e-network/neo-price-feed/actions
- Use `scripts/check-workflow-status.py` to check recent runs
- Use `scripts/trigger-workflow.sh` to manually trigger workflows