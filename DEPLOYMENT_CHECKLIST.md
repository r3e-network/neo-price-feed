# Neo Price Feed - Production Deployment Checklist

## Pre-Deployment Verification

### 1. ✅ Code Review Completed
- [x] All critical security issues resolved
- [x] No hardcoded secrets in configuration files
- [x] All unit tests passing
- [x] Code formatting applied

### 2. ✅ Configuration Files Ready
- [x] `appsettings.json` - Default configuration
- [x] `appsettings.Production.json` - Production settings
- [x] `appsettings.accessible.json` - Public API configuration
- [x] `.env.example` - Environment variable template

### 3. ✅ Contract Deployed
- [x] Contract Hash: `0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc`
- [x] Network: Neo N3 TestNet
- [x] Deployment verified on explorer

## Deployment Steps

### Step 1: Set Environment Variables
```bash
# Required for production
export TEE_ACCOUNT_ADDRESS="your-tee-account-address"
export TEE_ACCOUNT_PRIVATE_KEY="your-tee-account-private-key"
export MASTER_ACCOUNT_ADDRESS="your-master-account-address"
export MASTER_ACCOUNT_PRIVATE_KEY="your-master-account-private-key"

# Optional API keys
export COINMARKETCAP_API_KEY="your-api-key"
export COINGECKO_API_KEY="your-api-key"
export KRAKEN_API_KEY="your-api-key"

# Monitoring (optional)
export OTLP_ENDPOINT="your-monitoring-endpoint"
```

### Step 2: Initialize Contract (One-time Setup)
```bash
# Follow INITIALIZATION_GUIDE.md
# 1. Open neo-cli
# 2. Initialize contract with admin accounts
# 3. Add TEE account as oracle
# 4. Set minimum oracles
```

### Step 3: Build and Test
```bash
# Build the project
dotnet build --configuration Release

# Run unit tests
dotnet test --configuration Release

# Test with mock data
dotnet run --project src/PriceFeed.Console -- --test-mock-price-feed
```

### Step 4: Deploy Application
```bash
# For development/testing
dotnet run --project src/PriceFeed.Console

# For production with specific environment
ASPNETCORE_ENVIRONMENT=Production dotnet run --project src/PriceFeed.Console

# Or use the published binaries
dotnet publish -c Release -o ./publish
./publish/PriceFeed.Console
```

### Step 5: Verify Deployment
```bash
# Check contract status
bash scripts/check-contract-status.sh

# Monitor logs
tail -f logs/pricefeed-*.log

# Query prices via neo-cli
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc getPrice ["BTCUSDT"]
```

## GitHub Actions Deployment

### 1. Set GitHub Secrets
Navigate to Settings > Secrets and variables > Actions:
- `NEO_TEE_ACCOUNT_ADDRESS`
- `NEO_TEE_ACCOUNT_PRIVATE_KEY`
- `NEO_MASTER_ACCOUNT_ADDRESS`
- `NEO_MASTER_ACCOUNT_PRIVATE_KEY`
- `COINMARKETCAP_API_KEY` (optional)

### 2. Enable Scheduled Workflow
The price feed workflow runs:
- Every 5 minutes (via cron schedule)
- On manual trigger (workflow_dispatch)

### 3. Monitor Workflow Runs
- Check Actions tab for execution status
- Review logs for any errors
- Verify price updates on blockchain

## Post-Deployment Verification

### 1. Health Checks
- [ ] All data sources responding
- [ ] Neo RPC connection stable
- [ ] Price updates being submitted
- [ ] Attestations being generated

### 2. Monitoring
- [ ] Logs being collected
- [ ] Metrics being exported
- [ ] Alerts configured
- [ ] Error rates acceptable

### 3. Security
- [ ] No sensitive data in logs
- [ ] Private keys secure
- [ ] Access controls verified
- [ ] Audit trail enabled

## Rollback Plan

If issues occur:

1. **Stop the service**
   ```bash
   # Kill the process or stop the container
   pkill -f PriceFeed.Console
   ```

2. **Check contract state**
   ```bash
   # Verify contract is not corrupted
   bash scripts/check-contract-status.sh
   ```

3. **Review logs**
   ```bash
   # Check for errors
   grep ERROR logs/pricefeed-*.log
   ```

4. **Restore previous version**
   ```bash
   # Checkout previous commit
   git checkout <previous-commit-hash>
   dotnet build && dotnet run
   ```

## Maintenance Tasks

### Daily
- [ ] Check price update frequency
- [ ] Review error logs
- [ ] Monitor API rate limits

### Weekly
- [ ] Review attestation files
- [ ] Check disk space
- [ ] Verify backup processes

### Monthly
- [ ] Rotate API keys
- [ ] Update dependencies
- [ ] Performance review
- [ ] Security audit

## Support Contacts

- **Contract Issues**: Check INITIALIZATION_GUIDE.md
- **API Issues**: Review API_ACCESSIBILITY.md
- **Deployment Issues**: Check deployment logs
- **Security Issues**: Follow security protocols

---

*Last Updated: 2025-07-12*
*Version: 1.0.0*